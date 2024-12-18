import os
import sys
from loguru import logger
import threading
from queue import Queue, Empty
import time
from typing import Dict, List, Optional, Union
import platform
import subprocess
from scapy.all import sniff, IP, TCP
import psutil
import hashlib
from datetime import datetime
import re
import yaml
import json
import requests

# Optional imports
try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    logger.warning("Yara module not available. Some features will be disabled.")
    YARA_AVAILABLE = False

try:
    from elasticsearch import Elasticsearch
    ES_AVAILABLE = True
except ImportError:
    logger.warning("Elasticsearch not available. Some features will be disabled.")
    ES_AVAILABLE = False

try:
    from prometheus_client import start_http_server, Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("Prometheus client not available. Metrics collection will be disabled.")
    PROMETHEUS_AVAILABLE = False

try:
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    ML_AVAILABLE = True
except ImportError:
    logger.warning("Machine learning modules not available. Some features will be disabled.")
    ML_AVAILABLE = False

try:
    from suricata.sc import SuricataCtx
    SURICATA_AVAILABLE = True
except ImportError:
    logger.warning("Suricata not available. IDS features will be limited.")
    SURICATA_AVAILABLE = False

try:
    from ossec import Ossec
    OSSEC_AVAILABLE = True
except ImportError:
    logger.warning("OSSEC not available. HIDS features will be limited.")
    OSSEC_AVAILABLE = False

try:
    from zeek import ZeekControl
    ZEEK_AVAILABLE = True
except ImportError:
    logger.warning("Zeek not available. Network monitoring will be limited.")
    ZEEK_AVAILABLE = False

class DefensiveTools:
    def __init__(self, config: Dict):
        """Initialize defensive security tools"""
        self.config = config
        self.initialize_components()
        self.setup_monitoring()
        
    def initialize_components(self):
        """Initialize all defensive components"""
        # Initialize core components
        self.event_queue = Queue()
        self.alert_queue = Queue()
        self.monitoring = False
        self.packet_capture = False
        self.running = False
        
        # Initialize advanced components
        self.initialize_ids()
        self.initialize_threat_detection()
        self.initialize_ml_models()
        self.initialize_metrics()
        self.initialize_storage()
        
    def initialize_ids(self):
        """Initialize Intrusion Detection Systems"""
        try:
            # Initialize Suricata IDS
            suricata_config = self.config.get('suricata', {})
            if suricata_config and SURICATA_AVAILABLE:
                self.suricata = SuricataCtx(suricata_config['config_path'])
                self.suricata.load_rules(suricata_config['rules_path'])
            
            # Initialize OSSEC HIDS
            ossec_config = self.config.get('ossec', {})
            if ossec_config and OSSEC_AVAILABLE:
                self.ossec = Ossec(ossec_config['config_path'])
            
            # Initialize Zeek Network Analysis
            zeek_config = self.config.get('zeek', {})
            if zeek_config and ZEEK_AVAILABLE:
                self.zeek = ZeekControl()
                self.zeek.load_scripts(zeek_config['scripts_path'])
        except Exception as e:
            logger.error(f"Failed to initialize IDS components: {e}")
            
    def initialize_threat_detection(self):
        """Initialize threat detection components"""
        try:
            # Initialize YARA rules
            rules_path = self.config.get('yara_rules_path')
            if rules_path and os.path.exists(rules_path) and YARA_AVAILABLE:
                self.yara_rules = {}
                for rule_file in os.listdir(rules_path):
                    if rule_file.endswith('.yar'):
                        rule_path = os.path.join(rules_path, rule_file)
                        self.yara_rules[rule_file] = yara.compile(rule_path)
            
            # Initialize threat intelligence feeds
            self.threat_feeds = self.config.get('threat_feeds', [])
            self.ioc_database = self.load_threat_feeds()
            
        except Exception as e:
            logger.error(f"Failed to initialize threat detection: {e}")
            
    def initialize_ml_models(self):
        """Initialize machine learning models"""
        try:
            # Initialize anomaly detection
            if ML_AVAILABLE:
                self.ml_models = {
                    'network_anomaly': IsolationForest(contamination=0.1),
                    'behavior_anomaly': IsolationForest(contamination=0.05)
                }
            
            # Load pre-trained models if available
            model_path = self.config.get('ml_models_path')
            if model_path and os.path.exists(model_path) and ML_AVAILABLE:
                self.load_pretrained_models(model_path)
                
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")
            
    def initialize_metrics(self):
        """Initialize Prometheus metrics"""
        try:
            # Start Prometheus metrics server
            metrics_port = self.config.get('metrics_port', 9090)
            if PROMETHEUS_AVAILABLE:
                start_http_server(metrics_port)
            
            # Define metrics
            if PROMETHEUS_AVAILABLE:
                self.metrics = {
                    'events_total': Counter('siem_events_total', 'Total number of security events'),
                    'alerts_total': Counter('siem_alerts_total', 'Total number of security alerts'),
                    'threat_score': Gauge('siem_threat_score', 'Current threat score'),
                    'response_time': Histogram('siem_response_time', 'Response time for security events')
                }
        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")
            
    def initialize_storage(self):
        """Initialize storage backends"""
        try:
            # Initialize Elasticsearch
            es_config = self.config.get('elasticsearch', {})
            if es_config and ES_AVAILABLE:
                self.es_client = Elasticsearch(
                    [es_config['host']],
                    http_auth=(es_config['user'], es_config['password'])
                )
                
            # Initialize other storage backends as needed
            # Example: Redis for real-time alerts
            
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            
    def setup_monitoring(self):
        """Setup monitoring components"""
        # Initialize monitoring threads
        self.threads = []
        
        # Network monitoring thread
        self.threads.append(threading.Thread(
            target=self._network_monitor,
            daemon=True,
            name="NetworkMonitor"
        ))
        
        # System monitoring thread
        self.threads.append(threading.Thread(
            target=self._system_monitor,
            daemon=True,
            name="SystemMonitor"
        ))
        
        # File integrity monitoring thread
        self.threads.append(threading.Thread(
            target=self._file_integrity_monitor,
            daemon=True,
            name="FileMonitor"
        ))
        
        # Alert processing thread
        self.threads.append(threading.Thread(
            target=self._process_alerts,
            daemon=True,
            name="AlertProcessor"
        ))
        
    def start_monitoring(self):
        """Start all monitoring threads"""
        logger.info("Starting defensive monitoring")
        self.monitoring = True
        self.running = True
        
        for thread in self.threads:
            try:
                thread.start()
                logger.info(f"Started {thread.name}")
            except Exception as e:
                logger.error(f"Failed to start {thread.name}: {e}")
                
        # Start packet capture if available
        if self._check_pcap_available():
            self.start_packet_capture()
            
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        logger.info("Stopping defensive monitoring")
        self.monitoring = False
        self.running = False
        self.packet_capture = False
        
        for thread in self.threads:
            try:
                thread.join(timeout=5)
                logger.info(f"Stopped {thread.name}")
            except Exception as e:
                logger.error(f"Error stopping {thread.name}: {e}")
                
    def _check_pcap_available(self) -> bool:
        """Check if packet capture is available"""
        try:
            from scapy.all import conf
            if conf.L2listen() is not None:
                return True
        except Exception:
            pass
        return False
        
    def start_packet_capture(self):
        """Start packet capture"""
        if self._check_pcap_available():
            self.packet_capture = True
            threading.Thread(
                target=self._packet_capture,
                daemon=True,
                name="PacketCapture"
            ).start()
            logger.info("Started packet capture")
        else:
            logger.warning("Packet capture not available")
            
    def _packet_capture(self):
        """Capture and analyze network packets"""
        def packet_callback(packet):
            if not self.packet_capture:
                return
            
            if IP in packet:
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                
                # Check for suspicious patterns
                if self._is_suspicious_traffic(packet):
                    self.suspicious_ips.add(src_ip)
                    self._raise_alert({
                        'type': 'suspicious_traffic',
                        'source_ip': src_ip,
                        'destination_ip': dst_ip,
                        'timestamp': datetime.now().isoformat()
                    })
                    
        try:
            sniff(prn=packet_callback, store=0)
        except Exception as e:
            logger.error(f"Packet capture error: {e}")
            
    def _network_monitor(self):
        """Monitor network connections"""
        while self.monitoring:
            try:
                connections = psutil.net_connections()
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        remote_ip = conn.raddr.ip if conn.raddr else None
                        if remote_ip and self._is_suspicious_ip(remote_ip):
                            self._raise_alert({
                                'type': 'suspicious_connection',
                                'ip': remote_ip,
                                'port': conn.raddr.port if conn.raddr else None,
                                'timestamp': datetime.now().isoformat()
                            })
                            
            except Exception as e:
                logger.error(f"Network monitoring error: {e}")
                
            time.sleep(5)
            
    def _system_monitor(self):
        """Monitor system resources"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > self.thresholds['cpu_usage_threshold']:
                    self._raise_alert({
                        'type': 'high_cpu_usage',
                        'value': cpu_percent,
                        'threshold': self.thresholds['cpu_usage_threshold'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                # Memory usage
                memory = psutil.virtual_memory()
                if memory.percent > self.thresholds['memory_usage_threshold']:
                    self._raise_alert({
                        'type': 'high_memory_usage',
                        'value': memory.percent,
                        'threshold': self.thresholds['memory_usage_threshold'],
                        'timestamp': datetime.now().isoformat()
                    })

                # Disk usage
                for partition in psutil.disk_partitions():
                    usage = psutil.disk_usage(partition.mountpoint)
                    if usage.percent > self.thresholds['disk_usage_threshold']:
                        self._raise_alert({
                            'type': 'high_disk_usage',
                            'partition': partition.mountpoint,
                            'value': usage.percent,
                            'threshold': self.thresholds['disk_usage_threshold'],
                            'timestamp': datetime.now().isoformat()
                        })
                        
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                
            time.sleep(60)
            
    def _file_integrity_monitor(self):
        """Monitor critical files for changes"""
        file_hashes = {}
        monitored_paths = self.config.get('monitored_files', [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/sudoers',
            '/etc/hosts'
        ])
        
        def get_file_hash(filepath: str) -> Optional[str]:
            try:
                with open(filepath, 'rb') as f:
                    return hashlib.sha256(f.read()).hexdigest()
            except Exception:
                return None
                
        # Initialize file hashes
        for filepath in monitored_paths:
            if os.path.exists(filepath):
                file_hashes[filepath] = get_file_hash(filepath)
                
        while self.monitoring:
            try:
                for filepath in monitored_paths:
                    if os.path.exists(filepath):
                        current_hash = get_file_hash(filepath)
                        if filepath in file_hashes and current_hash != file_hashes[filepath]:
                            self._raise_alert({
                                'type': 'file_modified',
                                'file': filepath,
                                'timestamp': datetime.now().isoformat()
                            })
                        file_hashes[filepath] = current_hash
                        
            except Exception as e:
                logger.error(f"File monitoring error: {e}")
                
            time.sleep(300)
            
    def _process_alerts(self):
        """Process alerts from the queue"""
        while self.running:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._handle_alert(alert)
            except Empty:  
                continue
            except Exception as e:
                logger.error(f"Error processing alert: {e}")
                if not self.running:
                    break
                
    def _handle_alert(self, alert: Dict):
        """Handle different types of security alerts"""
        logger.warning(f"Security Alert: {alert}")
        
        # Add alert handling logic here
        alert_type = alert.get('type')
        
        if alert_type == 'suspicious_traffic':
            self._handle_suspicious_traffic(alert)
        elif alert_type == 'suspicious_connection':
            self._handle_suspicious_connection(alert)
        elif alert_type in ['high_cpu_usage', 'high_memory_usage', 'high_disk_usage']:
            self._handle_resource_alert(alert)
        elif alert_type == 'file_modified':
            self._handle_file_modification(alert)
            
    def _handle_suspicious_traffic(self, alert: Dict):
        """Handle suspicious traffic alerts"""
        source_ip = alert.get('source_ip')
        if source_ip:
            if source_ip in self.suspicious_ips:
                self.blocked_ips.add(source_ip)
                logger.warning(f"Blocked suspicious IP: {source_ip}")
                
    def _handle_suspicious_connection(self, alert: Dict):
        """Handle suspicious connection alerts"""
        ip = alert.get('ip')
        if ip:
            self.suspicious_ips.add(ip)
            logger.warning(f"Added IP to suspicious list: {ip}")
            
    def _handle_resource_alert(self, alert: Dict):
        """Handle resource usage alerts"""
        logger.warning(
            f"High resource usage: {alert.get('type')} at {alert.get('value')}% "
            f"(threshold: {alert.get('threshold')}%)"
        )
        
    def _handle_file_modification(self, alert: Dict):
        """Handle file modification alerts"""
        logger.warning(f"Critical file modified: {alert.get('file')}")
        
    def _is_suspicious_traffic(self, packet) -> bool:
        """Check if network traffic is suspicious"""
        if IP in packet and TCP in packet:
            # Check for common attack patterns
            flags = packet[TCP].flags
            if flags & 0x02:  # SYN flag
                return True
            if flags & 0x01:  # FIN flag
                return True
                
        return False
        
    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP address is suspicious"""
        return (
            ip in self.suspicious_ips or
            ip in self.blocked_ips
        )
        
    def _raise_alert(self, alert: Dict):
        """Add alert to processing queue"""
        self.alert_queue.put(alert)

    def start(self):
        """Start defensive tools"""
        logger.info("Starting defensive tools")
        self.start_monitoring()

    def stop(self):
        """Stop defensive tools"""
        logger.info("Stopping defensive tools")
        self.stop_monitoring()

    def monitor_system(self):
        """Start comprehensive system monitoring"""
        try:
            self.monitoring = True
            
            # Start monitoring threads
            threads = [
                threading.Thread(target=self._monitor_network, daemon=True),
                threading.Thread(target=self._monitor_processes, daemon=True),
                threading.Thread(target=self._monitor_files, daemon=True),
                threading.Thread(target=self._monitor_logs, daemon=True),
                threading.Thread(target=self._process_alerts, daemon=True)
            ]
            
            for thread in threads:
                thread.start()
                
            logger.info("All monitoring systems started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            self.monitoring = False
            
    def _monitor_network(self):
        """Monitor network traffic with advanced detection"""
        try:
            while self.monitoring:
                # Capture packets with Scapy
                sniff(prn=self._process_packet, store=0)
                
                # Process Suricata alerts
                if hasattr(self, 'suricata') and SURICATA_AVAILABLE:
                    alerts = self.suricata.get_alerts()
                    self._process_ids_alerts(alerts)
                    
                # Process Zeek logs
                if hasattr(self, 'zeek') and ZEEK_AVAILABLE:
                    logs = self.zeek.get_current_logs()
                    self._process_zeek_logs(logs)
                    
        except Exception as e:
            logger.error(f"Network monitoring error: {e}")
            
    def _process_packet(self, packet):
        """Process individual network packets"""
        try:
            if IP in packet:
                # Extract packet information
                packet_info = {
                    'timestamp': datetime.now().isoformat(),
                    'src_ip': packet[IP].src,
                    'dst_ip': packet[IP].dst,
                    'protocol': packet[IP].proto
                }
                
                # Add TCP-specific information
                if TCP in packet:
                    packet_info.update({
                        'src_port': packet[TCP].sport,
                        'dst_port': packet[TCP].dport,
                        'flags': packet[TCP].flags
                    })
                
                # Check against threat intelligence
                if self._check_threat_intel(packet_info):
                    self._generate_alert('network', packet_info)
                    
                # Perform ML-based anomaly detection
                if ML_AVAILABLE and self._detect_anomaly(packet_info):
                    self._generate_alert('anomaly', packet_info)
                    
                # Store packet info
                self._store_event('network', packet_info)
                
        except Exception as e:
            logger.error(f"Packet processing error: {e}")
            
    def _monitor_processes(self):
        """Monitor system processes with behavioral analysis"""
        try:
            while self.monitoring:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                    process_info = proc.info
                    
                    # Analyze process behavior
                    if self._analyze_process_behavior(process_info):
                        self._generate_alert('process', process_info)
                        
                    # Check for malware indicators
                    if self._check_malware_indicators(process_info):
                        self._generate_alert('malware', process_info)
                        
                time.sleep(1)  # Adjust monitoring interval
                
        except Exception as e:
            logger.error(f"Process monitoring error: {e}")
            
    def _monitor_files(self):
        """Monitor file system changes"""
        try:
            while self.monitoring:
                # Implement file integrity monitoring
                self._check_file_integrity()
                
                # Scan for malware
                self._scan_for_malware()
                
                # Monitor sensitive directories
                self._monitor_sensitive_dirs()
                
                time.sleep(5)  # Adjust monitoring interval
                
        except Exception as e:
            logger.error(f"File monitoring error: {e}")
            
    def _generate_alert(self, alert_type: str, data: Dict):
        """Generate and process security alerts"""
        try:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'type': alert_type,
                'severity': self._calculate_severity(data),
                'data': data,
                'threat_score': self._calculate_threat_score(data)
            }
            
            # Update metrics
            if PROMETHEUS_AVAILABLE:
                self.metrics['alerts_total'].inc()
                self.metrics['threat_score'].set(alert['threat_score'])
            
            # Store alert
            if ES_AVAILABLE:
                self._store_alert(alert)
            
            # Trigger response if needed
            if alert['severity'] >= self.config.get('auto_response_threshold', 8):
                self._trigger_response(alert)
                
        except Exception as e:
            logger.error(f"Alert generation error: {e}")
            
    def _trigger_response(self, alert: Dict):
        """Trigger automated response based on alert"""
        try:
            response_type = self._determine_response(alert)
            
            if response_type == 'block_ip':
                self._block_ip(alert['data'].get('src_ip'))
            elif response_type == 'kill_process':
                self._kill_malicious_process(alert['data'].get('pid'))
            elif response_type == 'isolate_system':
                self._isolate_system()
                
            # Log response action
            self._log_response_action(alert, response_type)
            
        except Exception as e:
            logger.error(f"Response trigger error: {e}")
            
    def _store_alert(self, alert: Dict):
        """Store alert in storage backend"""
        try:
            if ES_AVAILABLE:
                index_name = f"siem-alerts-{datetime.now().strftime('%Y.%m')}"
                self.es_client.index(
                    index=index_name,
                    body=alert
                )
        except Exception as e:
            logger.error(f"Alert storage error: {e}")
