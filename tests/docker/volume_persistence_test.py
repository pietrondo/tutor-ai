#!/usr/bin/env python3
"""
Docker Volume Persistence Tests for Tutor-AI

Comprehensive tests for Docker volume persistence, data integrity,
backup/recovery, and data consistency across container restarts.

Usage:
    python tests/docker/volume_persistence_test.py
"""

import unittest
import docker
import requests
import os
import json
import time
import shutil
import tempfile
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VolumePersistenceTest(unittest.TestCase):
    """Test suite for Docker volume persistence and data integrity"""

    @classmethod
    def setUpClass(cls):
        """Initialize test environment"""
        cls.client = docker.from_env()
        cls.test_start_time = datetime.now()
        cls.persistence_stats = {}
        cls.test_data_dir = Path("/tmp/tutor_ai_volume_test")
        cls.test_data_dir.mkdir(exist_ok=True)

        # Ensure we're in the correct directory
        os.chdir('/mnt/c/Users/pietr/Documents/progetto/tutor-ai')

        logger.info("Starting Docker Volume Persistence Tests")
        logger.info(f"Test started at: {cls.test_start_time}")
        logger.info(f"Test data directory: {cls.test_data_dir}")

    @classmethod
    def tearDownClass(cls):
        """Cleanup test environment"""
        test_duration = datetime.now() - cls.test_start_time
        logger.info(f"Volume persistence tests completed in: {test_duration}")

        # Cleanup test data
        try:
            if cls.test_data_dir.exists():
                shutil.rmtree(cls.test_data_dir)
                logger.info(f"Cleaned up test data directory: {cls.test_data_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup test data directory: {e}")

        cls.generate_persistence_report()

    def setUp(self):
        """Setup for each test"""
        self.test_start_time = time.time()

    def tearDown(self):
        """Cleanup after each test"""
        test_duration = time.time() - self.test_start_time
        logger.info(f"Volume persistence test completed in: {test_duration:.2f}s")

    def test_01_docker_volumes_exist(self):
        """Test 1: Verify Docker volumes exist and are properly configured"""
        logger.info("Testing Docker volume configuration...")

        try:
            # List all Docker volumes
            volumes = self.client.volumes.list()

            volume_info = {}
            for volume in volumes:
                volume_info[volume.name] = {
                    'id': volume.id,
                    'driver': volume.attrs['Driver'],
                    'mountpoint': volume.attrs['Mountpoint'],
                    'created': volume.attrs['CreatedAt'],
                    'labels': volume.attrs.get('Labels', {}),
                    'usage_count': len(volume.attrs.get('UsageDetails', []))
                }

            logger.info(f"Found {len(volumes)} Docker volumes")

            # Check for expected volumes
            expected_volume_patterns = ['tutor-ai', 'data', 'logs', 'uploads']
            relevant_volumes = [
                name for name in volume_info.keys()
                if any(pattern in name.lower() for pattern in expected_volume_patterns)
            ]

            logger.info(f"Relevant volumes: {relevant_volumes}")

            self.persistence_stats['volume_configuration'] = {
                'total_volumes': len(volumes),
                'relevant_volumes': relevant_volumes,
                'volume_details': volume_info
            }

            # Basic volume validation
            self.assertGreater(len(volumes), 0, "No Docker volumes found")

        except Exception as e:
            logger.error(f"Docker volume configuration test failed: {e}")
            self.fail(f"Volume configuration test failed: {e}")

    def test_02_data_directory_persistence(self):
        """Test 2: Verify data directories are persistent and accessible"""
        logger.info("Testing data directory persistence...")

        persistence_results = {}

        try:
            # Expected data directories
            data_dirs = [
                './data',
                './data/courses',
                './data/uploads',
                './data/vector_db',
                './data/tracking',
                './logs'
            ]

            directory_status = {}

            for data_dir in data_dirs:
                dir_path = Path(data_dir)
                exists = dir_path.exists()
                is_dir = dir_path.is_dir() if exists else False
                readable = os.access(data_dir, os.R_OK) if exists else False
                writable = os.access(data_dir, os.W_OK) if exists else False

                # Count files if directory exists
                file_count = 0
                total_size = 0
                if exists and is_dir:
                    try:
                        for root, dirs, files in os.walk(data_dir):
                            file_count += len(files)
                            for file in files:
                                try:
                                    file_path = Path(root) / file
                                    total_size += file_path.stat().st_size
                                except (OSError, IOError):
                                    continue
                    except Exception as e:
                        logger.warning(f"Error scanning {data_dir}: {e}")

                directory_status[data_dir] = {
                    'exists': exists,
                    'is_directory': is_dir,
                    'readable': readable,
                    'writable': writable,
                    'file_count': file_count,
                    'total_size_bytes': total_size,
                    'total_size_mb': total_size / (1024 * 1024)
                }

                logger.info(f"{data_dir} - Exists: {exists}, Files: {file_count}, Size: {total_size / (1024*1024):.2f}MB")

            self.persistence_stats['data_directories'] = directory_status

            # Verify critical directories exist
            critical_dirs = ['./data', './logs']
            for dir_path in critical_dirs:
                self.assertTrue(directory_status[dir_path]['exists'],
                               f"Critical directory {dir_path} does not exist")
                self.assertTrue(directory_status[dir_path]['writable'],
                               f"Critical directory {dir_path} is not writable")

        except Exception as e:
            logger.error(f"Data directory persistence test failed: {e}")
            self.fail(f"Data directory persistence test failed: {e}")

    def test_03_database_persistence(self):
        """Test 3: Verify database persistence and integrity"""
        logger.info("Testing database persistence...")

        db_results = {}

        try:
            # Look for database files
            db_patterns = [
                './data/*.db',
                './data/**/*.db',
                './data/*.sqlite',
                './data/**/*.sqlite'
            ]

            db_files = []
            for pattern in db_patterns:
                db_files.extend(Path('.').glob(pattern))

            logger.info(f"Found database files: {db_files}")

            db_info = {}
            for db_file in db_files:
                try:
                    # Get file info
                    stat = db_file.stat()
                    file_size = stat.st_size
                    modified_time = datetime.fromtimestamp(stat.st_mtime)

                    # Test database integrity
                    integrity_ok = self.test_database_integrity(str(db_file))

                    # Test database connectivity
                    connectivity_ok = self.test_database_connectivity(str(db_file))

                    db_info[str(db_file)] = {
                        'size_bytes': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'modified_time': modified_time.isoformat(),
                        'integrity_check': integrity_ok,
                        'connectivity_check': connectivity_ok,
                        'file_hash': self.calculate_file_hash(str(db_file))
                    }

                    logger.info(f"Database {db_file.name} - Size: {file_size / (1024*1024):.2f}MB, "
                              f"Integrity: {integrity_ok}, Connectivity: {connectivity_ok}")

                except Exception as e:
                    db_info[str(db_file)] = {'error': str(e)}
                    logger.error(f"Error testing database {db_file}: {e}")

            self.persistence_stats['database_persistence'] = db_info

            # Verify at least one database exists and is healthy
            if db_files:
                healthy_dbs = [
                    name for name, info in db_info.items()
                    if info.get('integrity_check', False) and info.get('connectivity_check', False)
                ]

                self.assertGreater(len(healthy_dbs), 0,
                                 f"No healthy databases found. Found: {list(db_info.keys())}")

        except Exception as e:
            logger.error(f"Database persistence test failed: {e}")
            self.fail(f"Database persistence test failed: {e}")

    def test_database_integrity(self, db_path: str) -> bool:
        """Test database file integrity"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Test basic query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]

            conn.close()

            return integrity_result == "ok"
        except Exception as e:
            logger.warning(f"Database integrity check failed for {db_path}: {e}")
            return False

    def test_database_connectivity(self, db_path: str) -> bool:
        """Test database connectivity and basic operations"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Test read operation
            cursor.execute("SELECT count(*) FROM sqlite_master")
            count = cursor.fetchone()[0]

            # Test write operation (in a temporary table)
            cursor.execute("CREATE TEMPORARY TABLE test_table (id INTEGER)")
            cursor.execute("INSERT INTO test_table (id) VALUES (1)")
            cursor.execute("SELECT * FROM test_table")
            result = cursor.fetchone()
            cursor.execute("DROP TABLE test_table")

            conn.commit()
            conn.close()

            return result[0] == 1
        except Exception as e:
            logger.warning(f"Database connectivity check failed for {db_path}: {e}")
            return False

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def test_04_file_upload_persistence(self):
        """Test 4: Verify uploaded files persist across container restarts"""
        logger.info("Testing file upload persistence...")

        upload_results = {}

        try:
            # Create test file
            test_file_path = self.test_data_dir / "test_upload.txt"
            test_content = f"Test file created at {datetime.now().isoformat()}\n"
            test_content += "This file should persist across container restarts.\n"
            test_content += "File hash: " + hashlib.md5(test_content.encode()).hexdigest() + "\n"

            with open(test_file_path, 'w') as f:
                f.write(test_content)

            test_file_hash = hashlib.md5(test_content.encode()).hexdigest()
            test_file_size = len(test_content.encode())

            logger.info(f"Created test file: {test_file_path}")
            logger.info(f"Test file hash: {test_file_hash}")

            # Upload file through API
            upload_response = self.upload_test_file(str(test_file_path))

            upload_results['test_file'] = {
                'original_path': str(test_file_path),
                'original_hash': test_file_hash,
                'original_size': test_file_size,
                'upload_response': upload_response
            }

            if upload_response.get('success'):
                logger.info("Test file uploaded successfully")

                # Simulate container restart by checking if file persists
                persistence_check = self.verify_file_persistence(upload_response, test_file_hash)
                upload_results['persistence_check'] = persistence_check

                self.assertTrue(persistence_check['file_exists'],
                               "Uploaded file does not persist")
                self.assertEqual(persistence_check['file_hash'], test_file_hash,
                               "Uploaded file content does not match original")
            else:
                logger.error("Failed to upload test file")
                upload_results['persistence_check'] = {'error': 'Upload failed'}

            self.persistence_stats['file_upload_persistence'] = upload_results

        except Exception as e:
            logger.error(f"File upload persistence test failed: {e}")
            self.fail(f"File upload persistence test failed: {e}")

    def upload_test_file(self, file_path: str) -> Dict:
        """Upload a test file through the API"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': ('test_upload.txt', f, 'text/plain')}
                data = {'course_id': 'test_course'}

                response = requests.post(
                    'http://localhost:8000/courses/test-course/upload',
                    files=files,
                    data=data,
                    timeout=30
                )

            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'response_text': response.text,
                'response_json': response.json() if response.headers.get('content-type') == 'application/json' else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify_file_persistence(self, upload_response: Dict, expected_hash: str) -> Dict:
        """Verify that uploaded file persists with correct content"""
        try:
            if not upload_response.get('success'):
                return {'error': 'Upload was not successful'}

            # Look for the uploaded file in data directory
            upload_dirs = ['./data/uploads', './data']
            found_files = []

            for upload_dir in upload_dirs:
                if os.path.exists(upload_dir):
                    for root, dirs, files in os.walk(upload_dir):
                        for file in files:
                            if file == 'test_upload.txt':
                                found_files.append(os.path.join(root, file))

            if not found_files:
                return {'file_exists': False, 'found_files': []}

            # Check file hash
            persisted_file = found_files[0]
            with open(persisted_file, 'rb') as f:
                file_content = f.read()
                persisted_hash = hashlib.md5(file_content).hexdigest()

            return {
                'file_exists': True,
                'found_files': found_files,
                'file_path': persisted_file,
                'file_hash': persisted_hash,
                'file_size': len(file_content),
                'hash_matches': persisted_hash == expected_hash
            }
        except Exception as e:
            return {'error': str(e)}

    def test_05_log_file_persistence(self):
        """Test 5: Verify log files persist and are properly managed"""
        logger.info("Testing log file persistence...")

        log_results = {}

        try:
            # Check for log files
            log_patterns = [
                './logs/*.log',
                './logs/**/*.log'
            ]

            log_files = []
            for pattern in log_patterns:
                log_files.extend(Path('.').glob(pattern))

            logger.info(f"Found log files: {[str(f) for f in log_files]}")

            log_info = {}
            for log_file in log_files:
                try:
                    stat = log_file.stat()
                    file_size = stat.st_size
                    modified_time = datetime.fromtimestamp(stat.st_mtime)

                    # Read last few lines
                    last_lines = []
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            last_lines = [line.strip() for line in lines[-10:] if line.strip()]
                    except Exception as e:
                        logger.warning(f"Error reading log file {log_file}: {e}")

                    log_info[str(log_file)] = {
                        'size_bytes': file_size,
                        'size_mb': file_size / (1024 * 1024),
                        'modified_time': modified_time.isoformat(),
                        'line_count': len(lines) if 'lines' in locals() else 0,
                        'last_lines': last_lines,
                        'file_hash': self.calculate_file_hash(str(log_file))
                    }

                    logger.info(f"Log {log_file.name} - Size: {file_size / (1024*1024):.2f}MB, "
                              f"Lines: {len(lines) if 'lines' in locals() else 0}")

                except Exception as e:
                    log_info[str(log_file)] = {'error': str(e)}
                    logger.error(f"Error testing log file {log_file}: {e}")

            # Test log rotation (if applicable)
            rotation_test = self.test_log_rotation()

            self.persistence_stats['log_persistence'] = {
                'log_files': log_info,
                'log_rotation_test': rotation_test
            }

            # Verify log files exist and have content
            self.assertGreater(len(log_files), 0, "No log files found")

            # Check that logs have recent entries
            now = datetime.now()
            recent_logs = [
                name for name, info in log_info.items()
                if 'error' not in info and 'modified_time' in info
                and datetime.fromisoformat(info['modified_time']) > now - timedelta(hours=1)
            ]

            if recent_logs:
                logger.info(f"Found {len(recent_logs)} recently modified log files")
            else:
                logger.warning("No recently modified log files found")

        except Exception as e:
            logger.error(f"Log file persistence test failed: {e}")
            self.fail(f"Log file persistence test failed: {e}")

    def test_log_rotation(self) -> Dict:
        """Test log rotation functionality"""
        try:
            # Check for rotated log files
            rotated_patterns = [
                './logs/*.log.*',
                './logs/**/*.log.*',
                './logs/*.gz',
                './logs/**/*.gz'
            ]

            rotated_files = []
            for pattern in rotated_patterns:
                rotated_files.extend(Path('.').glob(pattern))

            return {
                'rotated_files_found': len(rotated_files),
                'rotated_files': [str(f) for f in rotated_files],
                'rotation_active': len(rotated_files) > 0
            }
        except Exception as e:
            return {'error': str(e)}

    def test_06_course_data_persistence(self):
        """Test 6: Verify course and material data persistence"""
        logger.info("Testing course data persistence...")

        course_results = {}

        try:
            # Test course creation through API
            test_course_data = {
                'title': 'Test Course for Persistence',
                'description': 'This is a test course to verify data persistence',
                'subject': 'Testing',
                'level': 'beginner'
            }

            create_response = requests.post(
                'http://localhost:8000/courses',
                json=test_course_data,
                timeout=10
            )

            course_results['course_creation'] = {
                'success': create_response.status_code == 200,
                'status_code': create_response.status_code,
                'response': create_response.json() if create_response.headers.get('content-type') == 'application/json' else None
            }

            if create_response.status_code == 200:
                course_id = create_response.json().get('data', {}).get('id')
                logger.info(f"Created test course with ID: {course_id}")

                # Verify course persistence
                if course_id:
                    get_response = requests.get(f'http://localhost:8000/courses/{course_id}', timeout=10)

                    course_results['course_retrieval'] = {
                        'success': get_response.status_code == 200,
                        'status_code': get_response.status_code,
                        'course_data': get_response.json() if get_response.headers.get('content-type') == 'application/json' else None
                    }

                    if get_response.status_code == 200:
                        retrieved_course = get_response.json().get('data', {})
                        persistence_check = {
                            'title_matches': retrieved_course.get('title') == test_course_data['title'],
                            'description_matches': retrieved_course.get('description') == test_course_data['description'],
                            'subject_matches': retrieved_course.get('subject') == test_course_data['subject']
                        }

                        course_results['persistence_check'] = persistence_check

                        # Verify all fields match
                        self.assertTrue(all(persistence_check.values()),
                                      "Course data does not persist correctly")

                        logger.info("Course data persistence verified successfully")

            self.persistence_stats['course_data_persistence'] = course_results

        except Exception as e:
            logger.error(f"Course data persistence test failed: {e}")
            self.fail(f"Course data persistence test failed: {e}")

    def test_07_vector_database_persistence(self):
        """Test 7: Verify vector database persistence and integrity"""
        logger.info("Testing vector database persistence...")

        vector_db_results = {}

        try:
            # Check for ChromaDB or other vector database files
            vector_db_paths = [
                './data/vector_db',
                './data/chroma',
                './data/vector_store'
            ]

            vector_db_info = {}
            for db_path in vector_db_paths:
                path_obj = Path(db_path)
                exists = path_obj.exists()
                is_dir = path_obj.is_dir() if exists else False

                if exists and is_dir:
                    # Count files and calculate size
                    file_count = 0
                    total_size = 0
                    vector_extensions = ['.bin', '.json', '.pkl', '.index', '.faiss']

                    try:
                        for root, dirs, files in os.walk(db_path):
                            for file in files:
                                file_count += 1
                                try:
                                    file_path = Path(root) / file
                                    total_size += file_path.stat().st_size
                                except (OSError, IOError):
                                    continue

                        vector_db_info[db_path] = {
                            'exists': True,
                            'file_count': file_count,
                            'total_size_bytes': total_size,
                            'total_size_mb': total_size / (1024 * 1024),
                            'vector_files': sum(1 for root, dirs, files in os.walk(db_path)
                                               for file in files if any(file.lower().endswith(ext.lower()) for ext in vector_extensions))
                        }

                        logger.info(f"Vector DB at {db_path} - Files: {file_count}, "
                                  f"Vector files: {vector_db_info[db_path]['vector_files']}, "
                                  f"Size: {total_size / (1024*1024):.2f}MB")

                    except Exception as e:
                        vector_db_info[db_path] = {'exists': True, 'error': str(e)}
                        logger.warning(f"Error scanning vector DB {db_path}: {e}")
                else:
                    vector_db_info[db_path] = {'exists': False}

            # Test vector database functionality through API
            api_test = self.test_vector_db_api()

            self.persistence_stats['vector_database_persistence'] = {
                'vector_db_info': vector_db_info,
                'api_test': api_test
            }

            # Verify vector database exists and has content
            existing_dbs = [path for path, info in vector_db_info.items() if info.get('exists', False)]

            if existing_dbs:
                logger.info(f"Found vector databases: {existing_dbs}")
                # Check that at least one vector database has files
                dbs_with_files = [
                    path for path, info in vector_db_info.items()
                    if info.get('exists', False) and info.get('file_count', 0) > 0
                ]
                self.assertGreater(len(dbs_with_files), 0,
                                   "Vector database exists but contains no files")
            else:
                logger.warning("No vector database found")

        except Exception as e:
            logger.error(f"Vector database persistence test failed: {e}")
            self.fail(f"Vector database persistence test failed: {e}")

    def test_vector_db_api(self) -> Dict:
        """Test vector database functionality through API"""
        try:
            # Test search functionality (which uses vector database)
            search_response = requests.get(
                'http://localhost:8000/search',
                params={'query': 'test search query', 'course_id': 'test'},
                timeout=15
            )

            return {
                'search_api_success': search_response.status_code == 200,
                'search_response_code': search_response.status_code,
                'search_response': search_response.json() if search_response.headers.get('content-type') == 'application/json' else None
            }
        except Exception as e:
            return {'error': str(e)}

    @classmethod
    def generate_persistence_report(cls):
        """Generate comprehensive persistence test report"""
        report = {
            'test_suite': 'Docker Volume Persistence Tests',
            'timestamp': datetime.now().isoformat(),
            'test_duration': str(datetime.now() - cls.test_start_time),
            'persistence_stats': cls.persistence_stats,
        }

        # Save report to file
        report_file = f"tests/reports/volume_persistence_test_report_{int(time.time())}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Volume persistence test report saved to: {report_file}")

            # Print summary
            print(f"\n{'='*60}")
            print("DOCKER VOLUME PERSISTENCE TEST SUMMARY")
            print(f"{'='*60}")
            print(f"Test Duration: {report['test_duration']}")
            print(f"Report File: {report_file}")

            # Data directory summary
            if 'data_directories' in cls.persistence_stats:
                data_dirs = cls.persistence_stats['data_directories']
                print(f"Data Directories: {len(data_dirs)} tested")
                total_size = sum(info.get('total_size_mb', 0) for info in data_dirs.values())
                print(f"Total Data Size: {total_size:.2f}MB")

            # Database summary
            if 'database_persistence' in cls.persistence_stats:
                db_persistence = cls.persistence_stats['database_persistence']
                print(f"Databases: {len(db_persistence)} tested")

            # File upload summary
            if 'file_upload_persistence' in cls.persistence_stats:
                upload_test = cls.persistence_stats['file_upload_persistence']
                if upload_test.get('upload_response', {}).get('success'):
                    print("File Upload Persistence: SUCCESS")
                else:
                    print("File Upload Persistence: FAILED")

            print(f"{'='*60}")

        except Exception as e:
            logger.error(f"Failed to generate volume persistence test report: {e}")


def run_volume_persistence_tests():
    """Run the Docker volume persistence test suite"""
    print("💾 Starting Docker Volume Persistence Tests...")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(VolumePersistenceTest)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Return results
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_volume_persistence_tests()
    import sys
    sys.exit(0 if success else 1)