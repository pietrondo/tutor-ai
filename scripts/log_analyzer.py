#!/usr/bin/env python3
"""
Tutor-AI Log Analysis Tool

Comprehensive log analysis and management utility for debugging and monitoring.
Provides real-time log monitoring, error analysis, performance metrics, and security insights.

Usage:
    python scripts/log_analyzer.py [command] [options]

Commands:
    monitor      Real-time log monitoring
    analyze      Analyze log files for insights
    errors       Show error statistics and trends
    performance  Analyze performance metrics
    security     Analyze security events
    search       Search logs for patterns
    export       Export logs to different formats
    cleanup      Clean up old log files
"""

import os
import sys
import json
import argparse
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import glob
import gzip
import signal
from collections import defaultdict, Counter
import time

class LogAnalyzer:
    """Main log analysis class"""

    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.running = True

        # Set up signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False

    def monitor_logs(self, follow: bool = True, filters: Optional[List[str]] = None):
        """Monitor logs in real-time"""
        print(f"📊 Starting log monitoring for: {self.log_dir}")
        print(f"🔍 Filters: {filters or 'None'}")
        print("Press Ctrl+C to stop monitoring\n")

        # Find all log files
        log_files = list(self.log_dir.glob("*.log"))

        if not log_files:
            print("❌ No log files found")
            return

        # Get file positions for monitoring
        file_positions = {str(f): f.stat().st_size for f in log_files}

        while self.running:
            for log_file in log_files:
                current_size = log_file.stat().st_size
                last_position = file_positions[str(log_file)]

                if current_size > last_position:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_position)
                        new_lines = f.readlines()

                        for line in new_lines:
                            if self._should_include_line(line, filters):
                                self._format_and_print_log_line(line, log_file.name)

                        file_positions[str(log_file)] = current_size

            time.sleep(0.5)  # Check every half second

    def analyze_logs(self, hours: int = 24, output_format: str = "text") -> Dict[str, Any]:
        """Analyze logs for comprehensive insights"""
        print(f"🔍 Analyzing logs from the last {hours} hours...")

        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Collect all relevant log entries
        log_entries = self._collect_log_entries(cutoff_time)

        if not log_entries:
            print("❌ No log entries found in the specified time range")
            return {}

        # Generate analysis
        analysis = {
            "summary": self._generate_summary(log_entries, cutoff_time),
            "errors": self._analyze_errors(log_entries),
            "performance": self._analyze_performance(log_entries),
            "api_metrics": self._analyze_api_metrics(log_entries),
            "security": self._analyze_security_events(log_entries),
            "top_endpoints": self._get_top_endpoints(log_entries),
            "user_activity": self._analyze_user_activity(log_entries),
            "trends": self._analyze_trends(log_entries)
        }

        # Output analysis
        self._output_analysis(analysis, output_format)

        return analysis

    def search_logs(self, pattern: str, context_lines: int = 3, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search logs for specific patterns"""
        print(f"🔍 Searching for pattern: {pattern}")

        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            print(f"❌ Invalid regex pattern: {e}")
            return []

        matches = []

        for log_file in self.log_dir.glob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                    for i, line in enumerate(lines):
                        if regex.search(line):
                            # Get context lines
                            start_idx = max(0, i - context_lines)
                            end_idx = min(len(lines), i + context_lines + 1)
                            context = lines[start_idx:end_idx]

                            matches.append({
                                "file": str(log_file),
                                "line_number": i + 1,
                                "match": line.strip(),
                                "context": [l.strip() for l in context],
                                "timestamp": self._extract_timestamp(line)
                            })
            except Exception as e:
                print(f"⚠️ Error reading {log_file}: {e}")

        print(f"✅ Found {len(matches)} matches")
        return matches

    def show_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Show comprehensive error statistics"""
        print(f"📈 Analyzing error statistics from the last {hours} hours...")

        cutoff_time = datetime.now() - timedelta(hours=hours)
        log_entries = self._collect_log_entries(cutoff_time)

        # Filter error entries
        error_entries = [entry for entry in log_entries if entry.get('level') in ['ERROR', 'FATAL', 'CRITICAL']]

        if not error_entries:
            print("✅ No errors found in the specified time range")
            return {}

        # Analyze errors
        error_stats = {
            "total_errors": len(error_entries),
            "error_rate": len(error_entries) / len(log_entries) * 100 if log_entries else 0,
            "error_types": Counter(entry.get('error_type', 'Unknown') for entry in error_entries),
            "error_messages": Counter(entry.get('message', 'No message') for entry in error_entries),
            "error_timeline": self._group_errors_by_time(error_entries),
            "affected_endpoints": self._get_affected_endpoints(error_entries),
            "error_sources": Counter(entry.get('logger', 'Unknown') for entry in error_entries),
            "critical_errors": [entry for entry in error_entries if entry.get('level') == 'CRITICAL']
        }

        # Display statistics
        self._display_error_statistics(error_stats)

        return error_stats

    def cleanup_logs(self, days: int = 30, dry_run: bool = False):
        """Clean up old log files"""
        print(f"🧹 Cleaning up log files older than {days} days...")

        cutoff_date = datetime.now() - timedelta(days=days)
        files_to_delete = []
        space_freed = 0

        # Find old log files
        for log_file in self.log_dir.glob("**/*"):
            if log_file.is_file() and log_file.stat().st_mtime < cutoff_date.timestamp():
                file_size = log_file.stat().st_size
                files_to_delete.append((log_file, file_size))
                space_freed += file_size

        if not files_to_delete:
            print("✅ No files to clean up")
            return

        print(f"📋 Found {len(files_to_delete)} files to delete ({space_freed / (1024*1024):.2f} MB)")

        if dry_run:
            print("🔍 DRY RUN - No files will be deleted")
            for file_path, size in files_to_delete[:10]:  # Show first 10
                print(f"  - {file_path} ({size / 1024:.2f} KB)")
            if len(files_to_delete) > 10:
                print(f"  ... and {len(files_to_delete) - 10} more files")
        else:
            deleted_count = 0
            for file_path, size in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Failed to delete {file_path}: {e}")

            print(f"✅ Deleted {deleted_count} files, freed {space_freed / (1024*1024):.2f} MB")

    def _collect_log_entries(self, since: datetime) -> List[Dict[str, Any]]:
        """Collect and parse log entries from all log files"""
        entries = []

        for log_file in self.log_dir.glob("*.log"):
            try:
                # Handle gzipped log files
                if log_file.suffix == '.gz':
                    with gzip.open(log_file, 'rt', encoding='utf-8', errors='ignore') as f:
                        entries.extend(self._parse_log_lines(f.readlines()))
                else:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        entries.extend(self._parse_log_lines(f.readlines()))
            except Exception as e:
                print(f"⚠️ Error reading {log_file}: {e}")

        # Filter by timestamp
        return [entry for entry in entries if entry.get('timestamp') and entry['timestamp'] >= since]

    def _parse_log_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Parse log lines into structured entries"""
        entries = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            entry = self._parse_log_line(line)
            if entry:
                entries.append(entry)

        return entries

    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line"""
        try:
            # Try JSON format first
            if line.startswith('{'):
                data = json.loads(line)
                if 'timestamp' in data:
                    data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                return data

            # Fallback to text parsing
            return self._parse_text_log_line(line)
        except Exception:
            return {
                'raw_line': line,
                'timestamp': datetime.now(),
                'level': 'UNKNOWN',
                'message': line,
                'logger': 'unknown'
            }

    def _parse_text_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse text-based log lines"""
        # Example format: 2024-01-01 12:00:00 | INFO | correlation_id | module:function:line | message
        pattern = r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\s]*)\s*\|\s*(\w+)\s*\|\s*([^\s]*)\s*\|\s*([^\s]*)\s*\|\s*(.*)'
        match = re.match(pattern, line)

        if match:
            timestamp_str, level, correlation_id, location, message = match.groups()
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
            except ValueError:
                timestamp = datetime.now()

            return {
                'timestamp': timestamp,
                'level': level.upper(),
                'correlation_id': correlation_id,
                'location': location,
                'message': message,
                'raw_line': line
            }

        return None

    def _should_include_line(self, line: str, filters: Optional[List[str]]) -> bool:
        """Check if a line should be included based on filters"""
        if not filters:
            return True

        line_lower = line.lower()
        return any(filter_term.lower() in line_lower for filter_term in filters)

    def _format_and_print_log_line(self, line: str, filename: str):
        """Format and print a log line with color coding"""
        try:
            if line.startswith('{'):
                # JSON format
                data = json.loads(line)
                level = data.get('level', 'INFO')
                message = data.get('message', '')
                correlation_id = data.get('correlation_id', '')
            else:
                # Text format - extract level
                level_match = re.search(r'\|\s*(\w+)\s*\|', line)
                level = level_match.group(1) if level_match else 'INFO'
                message = line.split('|')[-1].strip() if '|' in line else line
                correlation_id = ''

            # Color coding
            colors = {
                'DEBUG': '\033[36m',      # Cyan
                'INFO': '\033[32m',       # Green
                'WARN': '\033[33m',       # Yellow
                'WARNING': '\033[33m',    # Yellow
                'ERROR': '\033[31m',      # Red
                'FATAL': '\033[35m',      # Magenta
                'CRITICAL': '\033[35m',   # Magenta
            }

            reset = '\033[0m'
            color = colors.get(level.upper(), '')

            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"{timestamp} |{color}{level:8}{reset}| {filename:15} | {correlation_id:8} | {message}")

        except Exception as e:
            print(f"Error formatting line: {e}")
            print(line)

    def _generate_summary(self, entries: List[Dict[str, Any]], since: datetime) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {
            "total_entries": len(entries),
            "time_range": f"{since.strftime('%Y-%m-%d %H:%M')} to {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "log_levels": dict(Counter(entry.get('level', 'UNKNOWN') for entry in entries)),
            "unique_loggers": len(set(entry.get('logger', 'unknown') for entry in entries)),
            "unique_correlation_ids": len(set(entry.get('correlation_id') for entry in entries if entry.get('correlation_id')))
        }

    def _analyze_errors(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns"""
        error_entries = [entry for entry in entries if entry.get('level') in ['ERROR', 'FATAL', 'CRITICAL']]

        return {
            "total_errors": len(error_entries),
            "error_rate": len(error_entries) / len(entries) * 100 if entries else 0,
            "top_errors": dict(Counter(entry.get('message', 'No message') for entry in error_entries).most_common(10)),
            "error_sources": dict(Counter(entry.get('logger', 'unknown') for entry in error_entries).most_common(5))
        }

    def _analyze_performance(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        performance_entries = [entry for entry in entries if 'duration_ms' in str(entry.get('metadata', {}))]

        durations = []
        for entry in performance_entries:
            metadata = entry.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    continue

            if 'duration_ms' in metadata:
                durations.append(metadata['duration_ms'])

        if not durations:
            return {"message": "No performance data found"}

        return {
            "total_requests": len(durations),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)],
            "slow_requests": len([d for d in durations if d > 1000])
        }

    def _analyze_api_metrics(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze API endpoint metrics"""
        api_entries = [entry for entry in entries if entry.get('category') == 'api']

        endpoints = defaultdict(list)
        for entry in api_entries:
            metadata = entry.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    continue

            path = metadata.get('path') or entry.get('path', 'unknown')
            status = metadata.get('status_code', 'unknown')

            endpoints[path].append({
                'status': status,
                'duration': metadata.get('duration_ms', 0)
            })

        metrics = {}
        for endpoint, requests in endpoints.items():
            metrics[endpoint] = {
                'total_requests': len(requests),
                'success_rate': len([r for r in requests if str(r['status']).startswith('2')]) / len(requests) * 100,
                'avg_duration': sum(r['duration'] for r in requests) / len(requests) if requests else 0,
                'status_codes': dict(Counter(r['status'] for r in requests))
            }

        return metrics

    def _analyze_security_events(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security events"""
        security_entries = [entry for entry in entries if 'security' in entry.get('category', '')]

        return {
            "total_security_events": len(security_entries),
            "event_types": dict(Counter(entry.get('metadata', {}).get('event_type', 'unknown') for entry in security_entries)),
            "suspicious_ips": list(set(entry.get('metadata', {}).get('client_ip') for entry in security_entries if entry.get('metadata', {}).get('client_ip')))
        }

    def _get_top_endpoints(self, entries: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get most accessed endpoints"""
        endpoint_counts = Counter()

        for entry in entries:
            if entry.get('category') == 'api':
                metadata = entry.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        continue

                path = metadata.get('path') or entry.get('path', 'unknown')
                endpoint_counts[path] += 1

        return [{"endpoint": endpoint, "count": count} for endpoint, count in endpoint_counts.most_common(limit)]

    def _analyze_user_activity(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user activity patterns"""
        user_entries = [entry for entry in entries if entry.get('category') == 'user']

        return {
            "total_user_actions": len(user_entries),
            "action_types": dict(Counter(entry.get('metadata', {}).get('action', 'unknown') for entry in user_entries)),
            "unique_users": len(set(entry.get('metadata', {}).get('user_id') for entry in user_entries))
        }

    def _analyze_trends(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends over time"""
        hourly_counts = defaultdict(int)
        error_trends = defaultdict(int)

        for entry in entries:
            hour = entry.get('timestamp').hour if entry.get('timestamp') else datetime.now().hour
            hourly_counts[hour] += 1

            if entry.get('level') in ['ERROR', 'FATAL', 'CRITICAL']:
                error_trends[hour] += 1

        return {
            "hourly_activity": dict(hourly_counts),
            "hourly_errors": dict(error_trends),
            "peak_hour": max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else 0
        }

    def _output_analysis(self, analysis: Dict[str, Any], output_format: str):
        """Output analysis results"""
        if output_format == "json":
            print(json.dumps(analysis, indent=2, default=str))
        else:
            self._print_text_analysis(analysis)

    def _print_text_analysis(self, analysis: Dict[str, Any]):
        """Print analysis results in text format"""
        print("\n" + "="*60)
        print("📊 LOG ANALYSIS REPORT")
        print("="*60)

        # Summary
        summary = analysis.get("summary", {})
        print(f"\n📈 SUMMARY:")
        print(f"  Total entries: {summary.get('total_entries', 0):,}")
        print(f"  Time range: {summary.get('time_range', 'Unknown')}")
        print(f"  Log levels: {summary.get('log_levels', {})}")

        # Errors
        errors = analysis.get("errors", {})
        print(f"\n❌ ERRORS:")
        print(f"  Total errors: {errors.get('total_errors', 0)}")
        print(f"  Error rate: {errors.get('error_rate', 0):.2f}%")

        # Performance
        perf = analysis.get("performance", {})
        if isinstance(perf, dict) and 'total_requests' in perf:
            print(f"\n⚡ PERFORMANCE:")
            print(f"  Total requests: {perf.get('total_requests', 0):,}")
            print(f"  Avg duration: {perf.get('avg_duration_ms', 0):.2f}ms")
            print(f"  P95 duration: {perf.get('p95_duration_ms', 0):.2f}ms")
            print(f"  Slow requests: {perf.get('slow_requests', 0)}")

        # Top endpoints
        top_endpoints = analysis.get("top_endpoints", [])
        if top_endpoints:
            print(f"\n🎯 TOP ENDPOINTS:")
            for endpoint in top_endpoints[:5]:
                print(f"  {endpoint['endpoint']}: {endpoint['count']} requests")

    def _display_error_statistics(self, error_stats: Dict[str, Any]):
        """Display error statistics in a readable format"""
        print("\n" + "="*60)
        print("🚨 ERROR STATISTICS")
        print("="*60)

        print(f"\n📊 Overview:")
        print(f"  Total errors: {error_stats['total_errors']:,}")
        print(f"  Error rate: {error_stats['error_rate']:.2f}%")

        print(f"\n🔍 Top Error Messages:")
        for message, count in error_stats['error_messages'].most_common(10):
            print(f"  {count:4d}x: {message[:80]}{'...' if len(message) > 80 else ''}")

        print(f"\n📂 Error Sources:")
        for source, count in error_stats['error_sources'].most_common(10):
            print(f"  {count:4d}x: {source}")

        if error_stats['critical_errors']:
            print(f"\n💀 Critical Errors ({len(error_stats['critical_errors'])}):")
            for error in error_stats['critical_errors'][:5]:
                print(f"  - {error.get('message', 'No message')[:100]}")

    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from log line"""
        try:
            if line.startswith('{'):
                data = json.loads(line)
                timestamp_str = data.get('timestamp')
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Extract timestamp from text format
                pattern = r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})'
                match = re.search(pattern, line)
                if match:
                    return datetime.fromisoformat(match.group(1).replace(' ', 'T'))
        except Exception:
            pass
        return None

    def export_logs(self, output_file: str, format: str = "json", hours: int = 24):
        """Export logs to different formats"""
        print(f"📤 Exporting logs to {output_file} in {format} format...")

        cutoff_time = datetime.now() - timedelta(hours=hours)
        log_entries = self._collect_log_entries(cutoff_time)

        output_path = Path(output_file)

        if format.lower() == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(log_entries, f, indent=2, default=str)
        elif format.lower() == "csv":
            import csv

            if log_entries:
                # Get all possible fields
                all_fields = set()
                for entry in log_entries:
                    all_fields.update(entry.keys())

                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
                    writer.writeheader()
                    writer.writerows(log_entries)
        else:
            # Plain text
            with open(output_path, 'w', encoding='utf-8') as f:
                for entry in log_entries:
                    f.write(f"{entry.get('timestamp', 'No timestamp')} | {entry.get('level', 'UNKNOWN')} | {entry.get('message', 'No message')}\n")

        print(f"✅ Exported {len(log_entries)} log entries to {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Tutor-AI Log Analysis Tool")
    parser.add_argument("command", choices=[
        "monitor", "analyze", "errors", "performance", "security",
        "search", "cleanup", "export"
    ], help="Command to execute")

    parser.add_argument("--log-dir", default="./logs", help="Log directory path")
    parser.add_argument("--hours", type=int, default=24, help="Time range in hours")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--pattern", help="Search pattern")
    parser.add_argument("--context", type=int, default=3, help="Context lines for search")
    parser.add_argument("--case-sensitive", action="store_true", help="Case sensitive search")
    parser.add_argument("--filters", nargs="*", help="Filter patterns")
    parser.add_argument("--follow", action="store_true", help="Follow log files (monitor mode)")
    parser.add_argument("--days", type=int, default=30, help="Days for cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for cleanup")
    parser.add_argument("--output", help="Output file for export")

    args = parser.parse_args()

    # Create analyzer
    analyzer = LogAnalyzer(args.log_dir)

    try:
        if args.command == "monitor":
            analyzer.monitor_logs(follow=args.follow, filters=args.filters)

        elif args.command == "analyze":
            analyzer.analyze_logs(hours=args.hours, output_format=args.format)

        elif args.command == "errors":
            analyzer.show_error_statistics(hours=args.hours)

        elif args.command == "search":
            if not args.pattern:
                print("❌ --pattern is required for search command")
                return
            matches = analyzer.search_logs(
                pattern=args.pattern,
                context_lines=args.context,
                case_sensitive=args.case_sensitive
            )

            for match in matches:
                print(f"\n📍 Found in {match['file']}:{match['line_number']}")
                print(f"🕒 {match['timestamp']}")
                print(f"📝 Match: {match['match']}")
                if match['context']:
                    print("📖 Context:")
                    for i, line in enumerate(match['context']):
                        marker = ">>> " if i == args.context else "    "
                        print(f"{marker}{line}")

        elif args.command == "cleanup":
            analyzer.cleanup_logs(days=args.days, dry_run=args.dry_run)

        elif args.command == "export":
            if not args.output:
                print("❌ --output is required for export command")
                return
            analyzer.export_logs(
                output_file=args.output,
                format=args.format,
                hours=args.hours
            )

        else:
            print(f"❌ Command '{args.command}' not implemented yet")

    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()