import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, List, Dict, Callable, Optional

from django.db import connection

logger = logging.getLogger(__name__)


class OrphanFilesFinder:
    def __init__(
        self,
        upload_dir: str,
        db_config: Dict,
        safety_margin_minutes: int = 60,
        progress_callback: Optional[Callable] = None
    ):
        self.upload_dir = Path(upload_dir)
        self.db_config = db_config
        self.safety_margin = timedelta(minutes=safety_margin_minutes)
        self.analysis_start_time = datetime.now()
        self.progress_callback = progress_callback

    def _update_progress(self, current: int, total: int, description: str = ""):
        """Met à jour la barre de progression si un callback est fourni"""
        if self.progress_callback:
            self.progress_callback.set_progress(current, total, description=description)

    def get_database_files(self) -> Set[str]:
        """Récupère la liste des fichiers depuis les tables de la base de données"""
        logger.info("Récupération des fichiers depuis la base de données...")
        self._update_progress(15, 100, "Récupération des fichiers depuis osis_document_upload...")

        cursor = connection.cursor()

        # Récupération depuis la table principale
        query_upload = """
            SELECT DISTINCT file
            FROM osis_document_upload
            WHERE file IS NOT NULL AND file != ''
        """
        cursor.execute(query_upload)
        files_upload = {row[0] for row in cursor.fetchall()}
        logger.info(f"Trouvé {len(files_upload)} fichiers dans osis_document_upload")

        self._update_progress(25, 100, "Récupération des fichiers depuis osis_document_modifiedupload...")

        # Récupération depuis la table de modifications
        query_modified = """
            SELECT DISTINCT file
            FROM osis_document_modifiedupload
            WHERE file IS NOT NULL AND file != '' 
        """
        cursor.execute(query_modified)
        files_modified = {row[0] for row in cursor.fetchall()}
        logger.info(f"Trouvé {len(files_modified)} fichiers dans osis_document_modifiedupload")

        # Union des deux ensembles
        all_files = files_upload.union(files_modified)
        cursor.close()

        logger.info(f"Total unique: {len(all_files)} fichiers dans la base de données")
        return all_files

    def scan_disk_files_batch(self, batch_paths: List[Path]) -> Set[str]:
        """Scanne un batch de fichiers sur le disque"""
        files = set()
        for file_path in batch_paths:
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < (self.analysis_start_time - self.safety_margin):
                    relative_path = str(file_path.relative_to(self.upload_dir))
                    files.add(relative_path)
        return files

    def get_disk_files(self) -> Set[str]:
        """Récupère la liste des fichiers présents sur le disque avec threading"""
        logger.info("Scan des fichiers sur le disque...")
        self._update_progress(35, 100, "Scan des fichiers sur le disque...")

        if not self.upload_dir.exists():
            raise FileNotFoundError(f"Le dossier {self.upload_dir} n'existe pas")

        # Collecte tous les fichiers
        all_files = []
        for root, dirs, files in os.walk(self.upload_dir):
            root_path = Path(root)
            for file in files:
                all_files.append(root_path / file)

        logger.info(f"Trouvé {len(all_files)} fichiers à analyser")

        # Traitement par batches avec threading
        disk_files = set()
        batch_size = 10000
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(0, len(all_files), batch_size):
                batch = all_files[i:i + batch_size]
                future = executor.submit(self.scan_disk_files_batch, batch)
                futures.append(future)

            for i, future in enumerate(futures):
                batch_files = future.result()
                disk_files.update(batch_files)
                progress = 35 + (i + 1) * 30 / len(futures)  # 35% à 65%
                self._update_progress(int(progress), 100, f"Traitement des fichiers... {i + 1}/{len(futures)} lots")

        logger.info(f"Trouvé {len(disk_files)} fichiers éligibles sur le disque")
        return disk_files

    def find_and_verify_orphan_files(self, disk_files: Set[str], db_files: Set[str]) -> Dict:
        """Trouve et vérifie les fichiers orphelins"""
        logger.info("Recherche des fichiers orphelins...")
        self._update_progress(70, 100, "Recherche des fichiers orphelins...")

        orphan_files = disk_files - db_files
        logger.info(f"Trouvé {len(orphan_files)} fichiers orphelins potentiels")

        if not orphan_files:
            return {
                'verified_orphans': set(),
                'total_size': 0,
                'detailed_orphans': []
            }

        self._update_progress(80, 100, "Vérification finale et calcul des tailles...")

        # Vérification finale et calcul des tailles
        cursor = connection.cursor()
        verified_orphans = set()
        detailed_orphans = []
        total_size = 0

        # Traitement par batches
        batch_size = 1000
        orphan_list = list(orphan_files)

        for i in range(0, len(orphan_list), batch_size):
            batch = orphan_list[i:i + batch_size]

            # Vérification en base de données
            placeholders = ','.join(['%s'] * len(batch))
            query = f"""
            SELECT file FROM (
                SELECT DISTINCT file FROM osis_document_upload
                WHERE file IS NOT NULL AND file != ''
                UNION
                SELECT DISTINCT file FROM osis_document_modifiedupload
                WHERE file IS NOT NULL AND file != ''
            ) AS all_files
            WHERE file IN ({placeholders})
            """
            cursor.execute(query, batch)
            found_files = {row[0] for row in cursor.fetchall()}

            batch_orphans = set(batch) - found_files
            verified_orphans.update(batch_orphans)

            # Calcul des tailles pour ce batch
            for file_path in batch_orphans:
                full_path = self.upload_dir / file_path
                if full_path.exists():
                    size = full_path.stat().st_size
                    total_size += size
                    detailed_orphans.append({
                        'path': file_path,
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2)
                    })

            progress = 80 + (i + len(batch)) * 10 / len(orphan_list)  # 80% à 90%
            self._update_progress(int(progress), 100, f"Vérification... {i + len(batch)}/{len(orphan_list)} fichiers")

        cursor.close()

        return {
            'verified_orphans': verified_orphans,
            'total_size': total_size,
            'detailed_orphans': detailed_orphans
        }

    def run_analysis_with_progress(self) -> Dict:
        """Exécute l'analyse complète avec rapport de progression"""
        logger.info("=== DÉBUT DE L'ANALYSE DES FICHIERS ORPHELINS ===")

        try:
            # 1. Récupération des fichiers de la base de données (15-30%)
            db_files = self.get_database_files()

            # 2. Scan des fichiers sur le disque (35-65%)
            disk_files = self.get_disk_files()

            # 3. Identification et vérification des orphelins (70-90%)
            orphan_results = self.find_and_verify_orphan_files(disk_files, db_files)

            self._update_progress(90, 100, "Génération du rapport final...")

            # Génération du rapport final
            detailed_report = {
                'analysis_timestamp': self.analysis_start_time.isoformat(),
                'db_files_count': len(db_files),
                'disk_files_count': len(disk_files),
                'orphan_files_count': len(orphan_results['verified_orphans']),
                'total_size_bytes': orphan_results['total_size'],
                'total_size_mb': round(orphan_results['total_size'] / (1024 * 1024), 2),
                'total_size_gb': round(orphan_results['total_size'] / (1024 * 1024 * 1024), 2),
                'orphan_files_detail': orphan_results['detailed_orphans']
            }

            return {
                'db_files_count': len(db_files),
                'disk_files_count': len(disk_files),
                'orphan_files_count': len(orphan_results['verified_orphans']),
                'total_orphan_size_bytes': orphan_results['total_size'],
                'detailed_report': detailed_report
            }

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            raise
