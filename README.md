# OSIS Document
OSIS-Document is a document management solution designed to provide secure storage and access control for documents within the OSIS ecosystem.

# Installation & Setup

## Prerequisites
- Python 3.11+ installed on your system
- pip (Python package manager)


## 1. Clone the Repository

```bash
git clone git@github.com:uclouvain/osis-document.git
cd osis-document
```

## 2.Create a Virtual Environment
```bash
python -m venv venv
```

## 3.Activate the Virtual Environment
On Windows:
```bash
# Command Prompt
venv\Scripts\activate

# PowerShell
venv\Scripts\Activate.ps1
```
On macOS/Linux:
```bash
source venv/bin/activate
```

## 4. Install Dependencies
```bash
pip install -r requirements.txt
```

## 5. Database Setup
```bash
# Run database migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser
```

## 6. Run the Development Server
```bash
python manage.py runserver
```
The application will be available at http://127.0.0.1:8000/



# Configuration

OSIS-Document can be configured using environment variables. Create a .env file in your project root or set these variables in your deployment environment.
### Server Configuration

#### `OSIS_DOCUMENT_BASE_URL`

- **Description:** The primary server's full URL where OSIS-Document is hosted. This URL is used for generating document access links and API endpoints.

```bash
OSIS_DOCUMENT_BASE_URL=https://yourserver.com/osis_document/
```

#### `OSIS_DOCUMENT_API_SHARED_SECRET`

- **Description:** A shared secret key used for secure communication between OSIS servers. **Important:** Change this value in production environments.

```bash
OSIS_DOCUMENT_API_SHARED_SECRET=your-secure-secret-key
```


#### `OSIS_DOCUMENT_DOMAIN_LIST`

- **Default:** `[]`
- **Description:** List of domains allowed to display raw files. Used for Content Security Policy when deploying across multiple servers.

```bash
OSIS_DOCUMENT_DOMAIN_LIST=127.0.0.1:8001 yourserver.com another-server.com
```


### Rate Limiting \& Upload Controls

#### `OSIS_DOCUMENT_UPLOAD_LIMIT`

- **Default:** `10/minute`
- **Description:** Rate limit for document uploads per user. Follows Django REST Framework throttling policy format. See [DRF Throttling Documentation](https://www.django-rest-framework.org/api-guide/throttling/#setting-the-throttling-policy).

```bash
OSIS_DOCUMENT_UPLOAD_LIMIT='10/minute'
```


#### `OSIS_DOCUMENT_MAX_UPLOAD_SIZE`

- **Default:** `52428800` (50MB)
- **Description:** Maximum file size allowed for uploads in bytes. Set to `None` to disable size limits.

```bash
OSIS_DOCUMENT_MAX_UPLOAD_SIZE=52428800
```


### File Type Validation

#### `OSIS_DOCUMENT_ALLOWED_EXTENSIONS`

- **Default:** `['pdf', 'txt', 'docx', 'doc', 'odt', 'png', 'jpg']`
- **Description:** List of file extensions allowed for upload.

```bash
OSIS_DOCUMENT_ALLOWED_EXTENSIONS=pdf txt docx doc odt png jpg
```


#### `ENABLE_MIMETYPE_VALIDATION`

- **Default:** `False`
- **Description:** Enable MIME type validation to ensure uploaded files match their declared extensions.

```bash
ENABLE_MIMETYPE_VALIDATION=False
```


### Token \& Document Lifecycle

#### `OSIS_DOCUMENT_TOKEN_MAX_AGE`

- **Default:** `900` (15 minutes)
- **Description:** Maximum age in seconds for access tokens. After this time, tokens expire and can no longer be used for viewing or modifying documents.

```bash
OSIS_DOCUMENT_TOKEN_MAX_AGE=900
```


#### `OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE`

- **Default:** `900` (15 minutes)
- **Description:** Maximum age in seconds for temporary uploads before they are eligible for deletion by cleanup tasks.

```bash
OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE=900
```


#### `OSIS_DOCUMENT_DELETED_UPLOAD_MAX_AGE`

- **Default:** `1296000` (15 days)
- **Description:** Maximum age in seconds for deleted uploads before they are permanently removed by cleanup tasks.

```bash
OSIS_DOCUMENT_DELETED_UPLOAD_MAX_AGE=1296000
```


#### `OSIS_DOCUMENT_EXPORT_EXPIRATION_POLICY_AGE`

- **Default:** `1296000` (15 days)
- **Description:** Maximum age in seconds for export files before they expire and are eligible for cleanup.

```bash
OSIS_DOCUMENT_EXPORT_EXPIRATION_POLICY_AGE=1296000
```


### Example .env File ([Full file](https://github.com/uclouvain/osis-document/blob/dev/.env)).

```bash
# Server Configuration
OSIS_DOCUMENT_BASE_URL=https://documents.yourorganization.com/
OSIS_DOCUMENT_API_SHARED_SECRET=your-production-secret-key
OSIS_DOCUMENT_DOMAIN_LIST=documents.yourorganization.com app.yourorganization.com

# Upload Controls
OSIS_DOCUMENT_UPLOAD_LIMIT='20/minute'
OSIS_DOCUMENT_MAX_UPLOAD_SIZE=104857600
OSIS_DOCUMENT_ALLOWED_EXTENSIONS=pdf docx doc txt png jpg jpeg

# Security & Validation
ENABLE_MIMETYPE_VALIDATION=True

# Document Lifecycle (in seconds)
OSIS_DOCUMENT_TOKEN_MAX_AGE=1800
OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE=1800
OSIS_DOCUMENT_DELETED_UPLOAD_MAX_AGE=2592000
OSIS_DOCUMENT_EXPORT_EXPIRATION_POLICY_AGE=2592000
```

> **Security Note:** Always use secure, unique values for `OSIS_DOCUMENT_API_SHARED_SECRET` in production environments.



# Using OSIS Document Component

The osis_document_components library offers a collection of frontend components designed 
to streamline document upload functionality in your Django applications. These components handle the communication with the OSIS-Document backend, providing a smooth user experience for document management operations.

See project: [osis-document-components](https://github.com/uclouvain/osis-document-components).


# OpenAPI schema generation

To ease generation, use the provided generator:
```console
./manage.py generateschema --urlconf=osis_document.urls --generator_class osis_document.api.schema.OsisDocumentSchemaGenerator --file osis-document/schema.yml
```

# Communication between servers

To communicate between two servers (e.g., with SDK-based code), requests are sent with the header `X-Api-Key`
containing the shared secret set in the server using the setting `OSIS_DOCUMENT_API_SHARED_SECRET`, so make sure it set. 

# Troubleshooting on Server-Side

## 1) Upload failed because of HTTP_409 - conflict: Mimetype mismatch
If the setting ENABLE_MIMETYPE_VALIDATION = True, the server will ensure that the uploaded file and the extension 
is correct. We use python-magic to ensure this check and python-magic use 'file' unix command. 
Sometimes, the database of 'file' command can be out-of-date and we can have false positive. 
To update the database, you can copy the content of the file osis_document/docs/ressources/magic into /etc/magic
