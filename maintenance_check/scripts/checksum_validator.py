import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable, Tuple, Set

from django.db import connection

logger = logging.getLogger(__name__)


class ChecksumValidator:
    def __init__(
        self,
        upload_dir: str,
        db_config: Dict,
        progress_callback: Optional[Callable[[int, Dict], None]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ):
        self.upload_dir = Path(upload_dir)
        self.db_config = db_config
        self.analysis_start_time = datetime.now()
        self.progress_callback = progress_callback
        self.from_date = from_date
        self.to_date = to_date

    def _update_progress(self, percentage: int, info: dict, ):
        """Met à jour la barre de progression si un callback est fourni"""
        if self.progress_callback:
            self.progress_callback(percentage=percentage, info=info)

    def get_database_files_with_hash(self) -> Set[Tuple[str, str,str]]:
        """Récupère la liste des fichiers depuis les tables de la base de données"""
        logger.info("Récupération des fichiers depuis la base de données...")
        self._update_progress(
            15,
            {
                "description": "Récupération des fichiers depuis la table osis_document_upload...",
            }
        )
        cursor = None
        try:
            cursor = connection.cursor()
            query_upload = """
                SELECT uuid, file, metadata->>'hash' as hash
                FROM osis_document_upload
                WHERE file IS NOT NULL AND file != '' AND metadata->>'hash' IS NOT NULL
            """

            params = []
            if self.from_date or self.to_date:
                date_conditions = []

                if self.from_date:
                    date_conditions.append("(uploaded_at >= %s OR modified_at >= %s)")
                    params.extend([self.from_date, self.from_date])

                if self.to_date:
                    date_conditions.append("(uploaded_at <= %s OR modified_at <= %s)")
                    params.extend([self.to_date, self.to_date])

                if date_conditions:
                    query_upload += " AND (" + " AND ".join(date_conditions) + ")"

            cursor.execute(query_upload, params)
            files_upload = {(row[0], row[1], row[2]) for row in cursor.fetchall()}

            msg_info = f"Récupération des fichiers ({len(files_upload)}) depuis la table osis_document_upload"
            if self.from_date or self.to_date:
                msg_info += f" (Filtre par date: {self.from_date} et {self.to_date})"

            logger.info(msg_info)
            self._update_progress(15,{"description": msg_info})
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des fichiers depuis la table osis_document_upload : {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
        return files_upload

    def check_files_integrity(
        self,
        db_files_with_hash: Set[Tuple[str, str,str]],
    ) -> Dict:
        """
        Vérifie l'intégrité des fichiers avec catégorisation

        Args:
            db_files_with_hash: Liste de tuples (uuid_fichier, fichier, hash)
        Returns:
            Dictionnaire avec les catégories de résultats
        """
        total_files = len(db_files_with_hash) if db_files_with_hash else 0
        processed = 0
        result = {
            'file_not_found': [],
            'hash_mismatch': [],
            'correct_count': 0,
            'db_files_count': total_files,
        }
        if total_files == 0:
            logger.warning("Aucun fichier à vérifier")
            return result

        logger.info(f"Début de la vérification de l'intégrité de {total_files} fichiers")
        for uuid_fichier, fichier, hash_db in db_files_with_hash:
            # Calcul de la progression (30-90% pour cette phase)
            progress_percentage = 30 + int((processed / total_files) * 60)
            self._update_progress(
                progress_percentage,
                {
                    "description": f"Vérification du fichier {processed}/{total_files}: {fichier}",
                    "current_file": fichier,
                    "processed": processed,
                    "total": total_files
                }
            )
            file_path = self.upload_dir / fichier

            # Vérification de l'existence du fichier
            if not file_path.exists():
                logger.warning(f"Fichier non trouvé: {file_path}")
                result['file_not_found'].append({
                    'uuid': uuid_fichier,
                    'file_path': str(file_path),
                    'relative_path': fichier,
                    'expected_hash': hash_db
                })
                continue

            # Calcul du hash du fichier sur disque
            calculated_hash = self.calculate_file_hash(str(file_path))
            if calculated_hash is None:
                logger.error(f"Impossible de calculer le hash pour: {file_path}")
                result['file_not_found'].append({
                    'uuid': uuid_fichier,
                    'file_path': str(file_path),
                    'relative_path': fichier,
                    'expected_hash': hash_db,
                    'error': 'Erreur lors du calcul du hash'
                })
                continue

            # Comparaison des hashs
            if hash_db and calculated_hash == hash_db:
                result['correct_count'] += 1
                logger.debug(f"Hash correct pour: {fichier}")
            else:
                logger.warning(f"Hash incorrect pour: {fichier}")
                result['hash_mismatch'].append({
                    'uuid': uuid_fichier,
                    'file_path': str(file_path),
                    'relative_path': fichier,
                    'expected_hash': hash_db,
                    'calculated_hash': calculated_hash
                })

        self._update_progress(
            90,
            {
                "description": "Vérification d'intégrité terminée",
                "processed": processed,
                "total": total_files,
                "correct": result['correct_count'],
                "errors": len(result['file_not_found']) + len(result['hash_mismatch'])
            }
        )

        logger.info(f"Vérification terminée: {result['correct_count']} fichiers corrects, "
                    f"{len(result['file_not_found'])} non trouvés, "
                    f"{len(result['hash_mismatch'])} avec hash incorrect")
        return result

    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calcule le hash SHA256 d'un fichier

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Hash SHA256 en hexadécimal ou None en cas d'erreur
        """
        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                hash_value = hashlib.sha256(file_content).hexdigest()
            return hash_value
        except Exception as e:
            return None


    def run_analysis_with_progress(self) -> Dict:
        """Exécute l'analyse complète avec rapport de progression"""

        logger.info("=== DÉBUT DE L'ANALYSE DE VALIDATION DU CHECKSUM DES FICHIERS ===")

        try:
            # 1. Récupération des fichiers et hash de la base de données (15-30%)
            db_files_with_hash = self.get_database_files_with_hash()

            # 2. Analyse du hash des fichiers
            results = self.check_files_integrity(db_files_with_hash)

            # 3. Génération du rapport
            self._update_progress(
                90,
                {
                    "description": "Génération du rapport final...",
                }
            )
            detailed_report = {
                'analysis_start_time_timestamp': self.analysis_start_time.isoformat(),
                'analysis_end_time_timestamp': datetime.now().isoformat(),
                **results,
            }
            return {
                'total_db_files': results['db_files_count'],
                'total_not_found_files': len(results['file_not_found']),
                'total_hash_mismatch_files': len(results['hash_mismatch']),
                'detailed_report': detailed_report
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            raise
