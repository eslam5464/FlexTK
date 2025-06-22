<a id="readme-top"></a>

[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]
[![Github][github-shield]][github-url]

# Flex Toolkit (flextk)

Flex Toolkit is a comprehensive Python command-line interface (CLI) tool and library that provides
a powerful collection of utilities for modern development workflows. From cloud storage management
to media processing, authentication, and data handling, FlexTK streamlines complex tasks with
an intuitive interface and extensive feature set.

## ✨ Key Features

### 🔐 Authentication & Security

- **Firebase Authentication**: Complete user management with email/password, phone number authentication
- **Token Management**: JWT token encoding/decoding and validation
- **Secure Configuration**: Encrypted configuration storage with password protection

### ☁️ Cloud Storage Management

- **Multi-Provider Support**: Google Cloud Storage, BlackBlaze B2, AWS S3
- **Google Drive Integration**: Full API support for file upload/download, folder management, permissions
- **Firestore Database**: Complete Firestore operations with document CRUD operations

### 💳 Payment Processing

- **Stripe Integration**: Payment intent creation, confirmation, and management
- **Secure Transactions**: Built-in error handling and logging for payment operations

### 🎥 Media Processing

- **Image Processing**: Advanced computer vision capabilities with OpenCV
  - Face detection using YOLO and SCRFD models
  - Person detection with configurable confidence thresholds
  - Image conversion, rotation, resizing, and grayscale conversion
  - Unsplash API integration for image search and download
- **Video Processing**: FFmpeg-powered video operations
  - Format conversion (MP4, AVI, MOV, MKV, TS)
  - Video trimming, cutting, and frame extraction
  - Metadata extraction and video analysis
- **Audio Processing**: Comprehensive audio manipulation
  - Format conversion (MP3, WAV, OGG, FLAC, M4A)
  - Audio trimming, cutting, and joining
  - Metadata extraction and audio analysis

### 📄 Document Processing

- **LibreOffice Integration**: Document conversion and processing
- **PDF Operations**: Document format conversion
- **Excel/CSV Handling**: Data processing with Pandas integration

### 🛠️ Development Utilities

- **File Operations**: Advanced file handling and manipulation
- **Network Utilities**: HTTP request handling and API interactions
- **Schema Validation**: Pydantic-based data validation and serialization
- **Logging System**: Structured JSON logging with configurable levels

### 📱 Application Management

- **Auto-Installation**: Automatic installation of required dependencies (FFmpeg, ImageMagick, LibreOffice)
- **Cross-Platform**: Support for Windows, macOS, and Linux
- **Package Managers**: Integration with Chocolatey (Windows) and Homebrew (macOS)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📦 Installation

### Prerequisites

- Python 3.12+
- Poetry (for dependency management)

### Quick Install

```bash
git clone https://github.com/eslam5464/FlexTK.git
cd FlexTK
pip install poetry
poetry install
poetry shell
```

### Alternative Installation

```bash
pip install .
```

## 🚀 Quick Start

### CLI Usage

```bash
# View available commands
flextk --help

# Configure cloud storage
flextk config gcs --bucket_name your-bucket --service_account path/to/service-account.json

# Upload file to Google Cloud Storage
flextk cloud gcs upload-file --file_path local/file.txt --bucket_path remote/path/

# Configure BlackBlaze B2
flextk config bb2 --app_id your-app-id --app_key your-app-key
```

### Library Usage

#### Image Processing

```python
from lib.utils.media.image import ImageProcessingOpenCV

# Initialize image processor
processor = ImageProcessingOpenCV("path/to/image.jpg")

# Detect faces with YOLO
processor.detect_faces_yolo(
    output_dir="output/",
    confidence_threshold=0.5,
    save_individual_faces=True
)

# Detect persons
processor.detect_persons(
    output_dir="output/",
    save_individual_persons=True
)

# Apply transformations
processor.resize_image(800, 600).convert_to_grayscale().save_image("output/processed.jpg")
```

#### Cloud Storage

```python
from lib.storage.buckets.gcs import GCS
from lib.schemas.google_bucket import ServiceAccount

# Initialize Google Cloud Storage
gcs = GCS("bucket-name", "path/to/service-account.json")

# Upload file
gcs.upload_file("local/file.txt", "remote/path/file.txt")

# Download file
gcs.download_file("remote/path/file.txt", "local/downloaded.txt")

# List files
files = gcs.get_files("folder/path/")
```

#### Firebase Integration

```python
from lib.auth.firebase import Firebase, FirebaseAuth
from lib.schemas.firebase import FirebaseServiceAccount

# Initialize Firebase
service_account = FirebaseServiceAccount.model_validate(service_account_dict)
firebase = Firebase(service_account)

# Get user by email
user = firebase.get_user_by_email("user@example.com")

# Send notification
firebase.notify_a_device("device_token", "Title", "Message content")

# Authentication
auth = FirebaseAuth("web_api_key")
response = auth.sign_in_email_and_password("email@example.com", "password")
```

#### Media Conversion

```python
from lib.utils.converters.video import convert_video_ffmpeg
from lib.utils.converters.audio import convert_audio_ffmpeg
from lib.utils.media.video import SupportedVideoFormat
from lib.utils.media.audio import SupportedAudioFormat

# Convert video
convert_video_ffmpeg(
    "input.avi",
    "output/",
    SupportedVideoFormat.mp4
)

# Convert audio
convert_audio_ffmpeg(
    "input.wav",
    "output/",
    SupportedAudioFormat.mp3
)
```

## 🏗️ Project Structure

```text
flextk/
├── cli/                          # Command-line interface
│   ├── cloud_storage/           # Cloud storage commands
│   └── configuration.py         # Configuration management
├── core/                        # Core functionality
│   ├── config.py               # Configuration handling
│   ├── helpers.py              # Helper functions
│   └── schema.py               # Core schemas
├── lib/                         # Main library
│   ├── auth/                   # Authentication modules
│   │   └── firebase.py         # Firebase authentication
│   ├── payment_gateway/        # Payment processing
│   │   └── stripe.py          # Stripe integration
│   ├── schemas/               # Data validation schemas
│   ├── storage/               # Storage providers
│   │   ├── buckets/          # Cloud bucket implementations
│   │   ├── firestore.py      # Firestore operations
│   │   └── google_drive.py   # Google Drive integration
│   ├── utils/                 # Utility modules
│   │   ├── apps/             # Application management
│   │   ├── converters/       # Media converters
│   │   ├── media/            # Media processing
│   │   └── operating_systems/ # OS-specific utilities
│   └── wrappers/             # Application wrappers
└── flex_tk.py                 # Main CLI entry point
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🔧 Configuration

### Initial Setup

```bash
# Set master password for configuration encryption
flextk config set-password

# Configure Google Cloud Storage
flextk config gcs \
  --bucket_name your-bucket-name \
  --service_account /path/to/service-account.json

# Configure BlackBlaze B2
flextk config bb2 \
  --app_id your-app-id \
  --app_key your-app-key

# Configure Unsplash API
flextk config unsplash \
  --app_id your-app-id \
  --access_key your-access-key \
  --secret_key your-secret-key
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📚 Supported Formats

### Video Formats

- MP4, AVI, MOV, MKV, TS

### Audio Formats

- MP3, WAV, OGG, FLAC, M4A

### Image Formats

- JPEG, PNG, BMP, TIFF, WebP

### Cloud Storage Providers

- Google Cloud Storage
- BlackBlaze B2
- AWS S3
- Google Drive

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🤖 AI/ML Features

### Computer Vision

- **YOLO Models**: Multiple YOLO versions for face and person detection
- **SCRFD Models**: State-of-the-art face detection
- **Confidence Thresholds**: Configurable detection sensitivity
- **Batch Processing**: Process multiple images efficiently

### Model Management

- **Automatic Download**: Models downloaded on first use
- **Caching**: Local model caching for performance
- **Multiple Backends**: Support for different AI frameworks

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🔍 Advanced Features

### Logging

- **Structured Logging**: JSON-formatted logs with metadata
- **Multiple Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **File Rotation**: Automatic log file management
- **Custom Formatters**: Extensible logging configuration

### Error Handling

- **Custom Exceptions**: Domain-specific error types
- **Retry Logic**: Automatic retry for transient failures
- **Graceful Degradation**: Fallback mechanisms for failed operations

### Performance

- **Async Operations**: Non-blocking I/O for better performance
- **Batch Processing**: Efficient handling of multiple files
- **Memory Management**: Optimized memory usage for large files
- **Progress Tracking**: Real-time progress for long operations

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📋 Requirements

### System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.12 or higher
- **Memory**: 4GB RAM minimum (8GB recommended for AI features)
- **Storage**: 2GB free space (additional space for models and cache)

### Optional Dependencies

FlexTK can automatically install these tools when needed:

- **FFmpeg**: For video/audio processing
- **ImageMagick**: For advanced image operations
- **LibreOffice**: For document conversion
- **Git**: For version control operations

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🛡️ Security

### Data Protection

- **Encryption**: All configuration data is encrypted using Fernet (AES 128)
- **Token Management**: Secure handling of authentication tokens
- **API Keys**: Safe storage and transmission of API credentials
- **Input Validation**: Comprehensive validation using Pydantic schemas

### Best Practices

- Use environment variables for sensitive configuration
- Regularly rotate API keys and tokens
- Enable logging for audit trails
- Use secure connections (HTTPS) for all API calls

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🔄 API Reference

### Core Classes

#### ImageProcessingOpenCV

```python
class ImageProcessingOpenCV:
    def __init__(self, image_path: str)
    def detect_faces_yolo(self, output_dir: str = None, **kwargs) -> Self
    def detect_persons(self, output_dir: str = None, **kwargs) -> Self
    def resize_image(self, width: int, height: int) -> Self
    def convert_to_grayscale(self) -> Self
    def save_image(self, image_path: str) -> Self
```

#### GCS (Google Cloud Storage)

```python
class GCS:
    def __init__(self, bucket_name: str, service_account: str)
    def upload_file(self, file_path: str, bucket_folder_path: str) -> BucketFile
    def download_file(self, bucket_file_path: str, download_directory: str) -> None
    def get_files(self, bucket_folder_path: str = "") -> list[BucketFile]
    def delete_files(self, file_paths: list[str]) -> None
```

#### Firebase

```python
class Firebase:
    def __init__(self, service_account: FirebaseServiceAccount)
    def get_user_by_email(self, email: str) -> UserRecord
    def notify_a_device(self, device_token: str, title: str, content: str) -> bool
    def notify_multiple_devices(self, device_tokens: list[str], title: str, content: str) -> int
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
poetry install --with dev

# Run all tests
pytest

# Run with coverage
pytest --cov=lib --cov-report=html

# Run specific test file
pytest tests/test_media_processing.py

# Run tests with verbose output
pytest -v
```

### Test Structure

```text
tests/
├── unit/                    # Unit tests
│   ├── test_media/         # Media processing tests
│   ├── test_storage/       # Storage provider tests
│   └── test_auth/          # Authentication tests
├── integration/            # Integration tests
├── fixtures/              # Test data and fixtures
└── conftest.py            # Test configuration
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🚀 Performance Optimization

### Media Processing

- **Batch Processing**: Process multiple files simultaneously
- **Memory Management**: Efficient handling of large media files
- **Model Caching**: Cache AI models locally to avoid re-downloading
- **Parallel Processing**: Utilize multiple CPU cores for intensive operations

### Cloud Operations

- **Connection Pooling**: Reuse connections for multiple operations
- **Retry Logic**: Automatic retry with exponential backoff
- **Chunked Uploads**: Handle large files efficiently
- **Compression**: Optimize transfer sizes

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🔌 Extensibility

### Custom Plugins

FlexTK supports custom plugins for extending functionality:

```python
# Custom media processor
from lib.utils.media.base import BaseMediaProcessor

class CustomImageProcessor(BaseMediaProcessor):
    def process(self, input_path: str, output_path: str) -> None:
        # Your custom processing logic
        pass
```

### Configuration Extensions

```python
# Custom configuration schema
from lib.schemas.base import BaseSchema

class CustomConfig(BaseSchema):
    api_endpoint: str
    timeout: int = 30
    retries: int = 3
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📊 Monitoring and Observability

### Application Logging

FlexTK provides comprehensive logging capabilities:

```python
from lib.logger import configure_logging

# Configure logging
configure_logging(level="INFO", format="json")

# Use in your code
import logging
logger = logging.getLogger(__name__)
logger.info("Operation completed", extra={"file_count": 10})
```

### Metrics

- **Processing Times**: Track operation duration
- **Success Rates**: Monitor API call success rates
- **Error Tracking**: Detailed error reporting with stack traces
- **Resource Usage**: Monitor memory and CPU usage

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🤝 Contributing

We welcome contributions to FlexTK! Here's how you can help:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/eslam5464/FlexTK.git
cd FlexTK

# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install

# Run tests to ensure everything works
pytest
```

### Contribution Guidelines

1. **Fork the Project**: Create your own fork of the repository
2. **Create a Feature Branch**: `git checkout -b feature/AmazingFeature`
3. **Write Tests**: Ensure your code is well-tested
4. **Follow Code Style**: Use Black for formatting and isort for imports
5. **Update Documentation**: Update README and docstrings as needed
6. **Commit Your Changes**: `git commit -m 'Add some AmazingFeature'`
7. **Push to the Branch**: `git push origin feature/AmazingFeature`
8. **Open a Pull Request**: Submit your changes for review

### Code Quality

- **Code Formatting**: Use `black` and `isort`
- **Type Hints**: Add type hints to all functions
- **Documentation**: Write clear docstrings
- **Testing**: Maintain >90% test coverage
- **Performance**: Consider performance implications

### Areas for Contribution

- 🐛 **Bug Fixes**: Help identify and fix issues
- 🚀 **New Features**: Add new cloud providers or media formats
- 📚 **Documentation**: Improve examples and guides
- 🧪 **Testing**: Increase test coverage
- 🔧 **Performance**: Optimize existing functionality
- 🌐 **Localization**: Add support for more languages

## 📄 License

Distributed under the MIT License. See `LICENSE` file for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📞 Contact

**Eslam Mohamed** - [LinkedIn](https://linkedin.com/in/eslam5464)

**Project Link**: [GitHub Repository](https://github.com/eslam5464/FlexTK)

**Documentation**: [Wiki](https://github.com/eslam5464/FlexTK/wiki)

**Issues**: [Bug Reports & Feature Requests](https://github.com/eslam5464/FlexTK/issues)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🙏 Acknowledgments

- **OpenAI**: For inspiring AI integration patterns
- **Google**: For comprehensive cloud APIs
- **FFmpeg**: For excellent media processing capabilities
- **Ultralytics**: For YOLO model implementations
- **Firebase**: For authentication and database services
- **Stripe**: For payment processing integration
- **The Open Source Community**: For continuous inspiration and support

---

**[⬆ Back to Top](#readme-top)**

<!-- MARKDOWN LINKS & IMAGES -->

[github-shield]: https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=fff&style=for-the-badge
[github-url]: https://github.com/eslam5464/FlexTK
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/eslam5464
[license-shield]: https://img.shields.io/github/license/eslam5464/FlexTK?style=for-the-badge
[license-url]: https://img.shields.io/github/license/eslam5464/FlexTK
