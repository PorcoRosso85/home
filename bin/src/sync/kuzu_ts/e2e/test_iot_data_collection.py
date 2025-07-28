"""
E2E Test: IoT Data Collection and Synchronization
IoTデータ収集・同期ユースケース

このテストは、実際のIoTシステムシナリオで
sync/kuzu_tsがどのように使われるかを示す「実行可能な仕様書」です。
"""

import asyncio
import json
import pytest
import uuid
import time
import random
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import kuzu


class IoTDevice:
    """IoTデバイスのシミュレーション"""
    
    def __init__(self, device_id: str, device_type: str, location: str):
        self.device_id = device_id
        self.device_type = device_type
        self.location = location
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp(prefix=f"kuzu_iot_{device_id}_")
        # Use in-memory database with 256MB buffer pool for time-series data
        self.db = kuzu.Database(":memory:", buffer_pool_size=256 * 1024 * 1024)
        self.conn = kuzu.Connection(self.db)
        self.is_online = True
        self.battery_level = 100.0
        self._initialize_schema()
        
    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, 'conn'):
            del self.conn
        if hasattr(self, 'db'):
            del self.db
        if hasattr(self, 'temp_dir'):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
        
    def _initialize_schema(self):
        """IoTデータスキーマを初期化"""
        # デバイスマスタ
        self.conn.execute("""
            CREATE NODE TABLE Device (
                id STRING,
                type STRING,
                location STRING,
                status STRING,
                battery_level DOUBLE,
                last_seen INT64,
                PRIMARY KEY(id)
            )
        """)
        
        # センサー定義
        self.conn.execute("""
            CREATE NODE TABLE Sensor (
                id STRING,
                device_id STRING,
                sensor_type STRING,
                unit STRING,
                min_value DOUBLE,
                max_value DOUBLE,
                PRIMARY KEY(id)
            )
        """)
        
        # 測定データ
        self.conn.execute("""
            CREATE NODE TABLE Measurement (
                id STRING,
                timestamp INT64,
                value DOUBLE,
                quality STRING,
                PRIMARY KEY(id)
            )
        """)
        
        # アラート
        self.conn.execute("""
            CREATE NODE TABLE Alert (
                id STRING,
                severity STRING,
                message STRING,
                timestamp INT64,
                acknowledged BOOLEAN,
                PRIMARY KEY(id)
            )
        """)
        
        # リレーションシップ
        self.conn.execute("CREATE REL TABLE HAS_SENSOR (FROM Device TO Sensor)")
        self.conn.execute("CREATE REL TABLE MEASURED_BY (FROM Measurement TO Sensor)")
        self.conn.execute("CREATE REL TABLE TRIGGERED_BY (FROM Alert TO Device)")
        self.conn.execute("CREATE REL TABLE RELATED_TO (FROM Alert TO Measurement)")
        
        # 自デバイスを登録
        self.conn.execute("""
            CREATE (d:Device {
                id: $id,
                type: $type,
                location: $location,
                status: 'online',
                battery_level: $battery,
                last_seen: $timestamp
            })
        """, {
            "id": self.device_id,
            "type": self.device_type,
            "location": self.location,
            "battery": self.battery_level,
            "timestamp": int(time.time() * 1000)
        })
        
    def add_sensor(self, sensor_type: str, unit: str, min_val: float, max_val: float):
        """センサーを追加"""
        sensor_id = f"sensor-{self.device_id}-{sensor_type}"
        
        self.conn.execute("""
            CREATE (s:Sensor {
                id: $id,
                device_id: $device_id,
                sensor_type: $sensor_type,
                unit: $unit,
                min_value: $min_value,
                max_value: $max_value
            })
        """, {
            "id": sensor_id,
            "device_id": self.device_id,
            "sensor_type": sensor_type,
            "unit": unit,
            "min_value": min_val,
            "max_value": max_val
        })
        
        # リレーションシップを作成
        self.conn.execute("""
            MATCH (d:Device {id: $device_id})
            MATCH (s:Sensor {id: $sensor_id})
            CREATE (d)-[:HAS_SENSOR]->(s)
        """, {"device_id": self.device_id, "sensor_id": sensor_id})
        
        return sensor_id
        
    def collect_measurement(self, sensor_type: str, value: float) -> Dict[str, Any]:
        """センサーデータを収集"""
        sensor_id = f"sensor-{self.device_id}-{sensor_type}"
        measurement_id = f"meas-{uuid.uuid4()}"
        timestamp = int(time.time() * 1000)
        
        # データ品質を評価
        quality = "good"
        if self.battery_level < 20:
            quality = "low_battery"
        elif not self.is_online:
            quality = "offline"
            
        # 測定値を保存
        self.conn.execute("""
            CREATE (m:Measurement {
                id: $id,
                timestamp: $timestamp,
                value: $value,
                quality: $quality
            })
        """, {
            "id": measurement_id,
            "timestamp": timestamp,
            "value": value,
            "quality": quality
        })
        
        # センサーとの関連付け
        self.conn.execute("""
            MATCH (m:Measurement {id: $measurement_id})
            MATCH (s:Sensor {id: $sensor_id})
            CREATE (m)-[:MEASURED_BY]->(s)
        """, {"measurement_id": measurement_id, "sensor_id": sensor_id})
        
        # デバイスのlast_seenを更新
        self.conn.execute("""
            MATCH (d:Device {id: $device_id})
            SET d.last_seen = $timestamp,
                d.battery_level = $battery
        """, {
            "device_id": self.device_id,
            "timestamp": timestamp,
            "battery": self.battery_level
        })
        
        return {
            "id": measurement_id,
            "device_id": self.device_id,
            "sensor_type": sensor_type,
            "timestamp": timestamp,
            "value": value,
            "quality": quality
        }
        
    def check_thresholds(self, sensor_type: str, value: float) -> Optional[Dict[str, Any]]:
        """閾値チェックとアラート生成"""
        sensor_id = f"sensor-{self.device_id}-{sensor_type}"
        
        # センサーの閾値を取得
        result = self.conn.execute("""
            MATCH (s:Sensor {id: $sensor_id})
            RETURN s.min_value as min_val, s.max_value as max_val
        """, {"sensor_id": sensor_id})
        
        if result.has_next():
            row = result.get_next()
            min_val, max_val = row[0], row[1]
            
            if value < min_val or value > max_val:
                # アラートを生成
                alert_id = f"alert-{uuid.uuid4()}"
                severity = "critical" if abs(value - min_val) > 10 or abs(value - max_val) > 10 else "warning"
                message = f"{sensor_type} value {value} is out of range [{min_val}, {max_val}]"
                
                self.conn.execute("""
                    CREATE (a:Alert {
                        id: $id,
                        severity: $severity,
                        message: $message,
                        timestamp: $timestamp,
                        acknowledged: false
                    })
                """, {
                    "id": alert_id,
                    "severity": severity,
                    "message": message,
                    "timestamp": int(time.time() * 1000)
                })
                
                # デバイスとの関連付け
                self.conn.execute("""
                    MATCH (a:Alert {id: $alert_id})
                    MATCH (d:Device {id: $device_id})
                    CREATE (a)-[:TRIGGERED_BY]->(d)
                """, {"alert_id": alert_id, "device_id": self.device_id})
                
                return {
                    "id": alert_id,
                    "device_id": self.device_id,
                    "severity": severity,
                    "message": message
                }
        
        return None
        
    def sync_measurement(self, measurement: Dict[str, Any]):
        """他のデバイスからの測定データを同期"""
        # 測定値が既に存在するかチェック
        result = self.conn.execute(
            "MATCH (m:Measurement {id: $id}) RETURN m",
            {"id": measurement["id"]}
        )
        
        if not result.has_next():
            # 新しい測定値を保存
            self.conn.execute("""
                CREATE (m:Measurement {
                    id: $id,
                    timestamp: $timestamp,
                    value: $value,
                    quality: $quality
                })
            """, measurement)
            
            # デバイスが存在しない場合は作成
            self.conn.execute("""
                MERGE (d:Device {id: $device_id})
            """, {"device_id": measurement["device_id"]})
            
            # センサーとの関連付け（sensor_typeから推測）
            if "sensor_type" in measurement:
                sensor_id = f"sensor-{measurement['device_id']}-{measurement['sensor_type']}"
                self.conn.execute("""
                    MATCH (m:Measurement {id: $measurement_id})
                    MATCH (s:Sensor {id: $sensor_id})
                    CREATE (m)-[:MEASURED_BY]->(s)
                """, {
                    "measurement_id": measurement["id"],
                    "sensor_id": sensor_id
                })
            
    def get_recent_measurements(self, sensor_type: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """最近の測定値を取得"""
        sensor_id = f"sensor-{self.device_id}-{sensor_type}"
        cutoff_time = int((time.time() - minutes * 60) * 1000)
        
        result = self.conn.execute("""
            MATCH (m:Measurement)-[:MEASURED_BY]->(s:Sensor {id: $sensor_id})
            WHERE m.timestamp > $cutoff_time
            RETURN m.id as id,
                   m.timestamp as timestamp,
                   m.value as value,
                   m.quality as quality
            ORDER BY m.timestamp DESC
        """, {"sensor_id": sensor_id, "cutoff_time": cutoff_time})
        
        measurements = []
        while result.has_next():
            row = result.get_next()
            measurements.append({
                "id": row[0],
                "timestamp": row[1],
                "value": row[2],
                "quality": row[3]
            })
            
        return measurements
        
    def simulate_battery_drain(self):
        """バッテリー消費をシミュレート"""
        if self.battery_level > 0:
            self.battery_level -= random.uniform(0.1, 0.5)
            self.battery_level = max(0, self.battery_level)
            
            if self.battery_level < 10:
                self.is_online = False


class IoTGateway:
    """IoTゲートウェイ（データ集約）のシミュレーション"""
    
    def __init__(self, gateway_id: str):
        self.gateway_id = gateway_id
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp(prefix=f"kuzu_gateway_{gateway_id}_")
        # Use in-memory database with 256MB buffer pool for time-series data
        self.db = kuzu.Database(":memory:", buffer_pool_size=256 * 1024 * 1024)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()
        
    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, 'conn'):
            del self.conn
        if hasattr(self, 'db'):
            del self.db
        if hasattr(self, 'temp_dir'):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
        
    def _initialize_schema(self):
        """ゲートウェイのスキーマを初期化（デバイスと同じ）"""
        # デバイススキーマと同じものを使用
        schemas = [
            """CREATE NODE TABLE Device (
                id STRING, type STRING, location STRING,
                status STRING, battery_level DOUBLE, last_seen INT64,
                PRIMARY KEY(id)
            )""",
            """CREATE NODE TABLE Sensor (
                id STRING, device_id STRING, sensor_type STRING,
                unit STRING, min_value DOUBLE, max_value DOUBLE,
                PRIMARY KEY(id)
            )""",
            """CREATE NODE TABLE Measurement (
                id STRING, timestamp INT64, value DOUBLE, quality STRING,
                PRIMARY KEY(id)
            )""",
            """CREATE NODE TABLE Alert (
                id STRING, severity STRING, message STRING,
                timestamp INT64, acknowledged BOOLEAN,
                PRIMARY KEY(id)
            )"""
        ]
        
        for schema in schemas:
            self.conn.execute(schema)
            
        # リレーションシップ
        self.conn.execute("CREATE REL TABLE HAS_SENSOR (FROM Device TO Sensor)")
        self.conn.execute("CREATE REL TABLE MEASURED_BY (FROM Measurement TO Sensor)")
        self.conn.execute("CREATE REL TABLE TRIGGERED_BY (FROM Alert TO Device)")
        
    def sync_measurement(self, measurement: Dict[str, Any]):
        """測定データを同期（IoTDeviceと同じメソッドを提供）"""
        # 測定値が既に存在するかチェック
        result = self.conn.execute(
            "MATCH (m:Measurement {id: $id}) RETURN m",
            {"id": measurement["id"]}
        )
        
        if not result.has_next():
            # 新しい測定値を保存
            self.conn.execute("""
                CREATE (m:Measurement {
                    id: $id,
                    timestamp: $timestamp,
                    value: $value,
                    quality: $quality
                })
            """, {
                "id": measurement["id"],
                "timestamp": measurement["timestamp"],
                "value": measurement["value"],
                "quality": measurement["quality"]
            })
            
            # デバイスが存在しない場合は作成
            self.conn.execute("""
                MERGE (d:Device {id: $device_id})
            """, {"device_id": measurement["device_id"]})
            
            # センサーとの関連付け（sensor_typeから推測）
            if "sensor_type" in measurement:
                sensor_id = f"sensor-{measurement['device_id']}-{measurement['sensor_type']}"
                # センサーが存在するか確認
                sensor_result = self.conn.execute(
                    "MATCH (s:Sensor {id: $sensor_id}) RETURN s",
                    {"sensor_id": sensor_id}
                )
                if sensor_result.has_next():
                    self.conn.execute("""
                        MATCH (m:Measurement {id: $measurement_id})
                        MATCH (s:Sensor {id: $sensor_id})
                        CREATE (m)-[:MEASURED_BY]->(s)
                    """, {
                        "measurement_id": measurement["id"],
                        "sensor_id": sensor_id
                    })
        
    def aggregate_device_data(self, device_id: str) -> Dict[str, Any]:
        """デバイスのデータを集約"""
        # デバイス情報
        device_result = self.conn.execute("""
            MATCH (d:Device {id: $device_id})
            RETURN d.type as type,
                   d.location as location,
                   d.status as status,
                   d.battery_level as battery
        """, {"device_id": device_id})
        
        device_info = None
        if device_result.has_next():
            row = device_result.get_next()
            device_info = {
                "device_id": device_id,
                "type": row[0],
                "location": row[1],
                "status": row[2],
                "battery_level": row[3]
            }
            
        # 最新測定値
        measurements_result = self.conn.execute("""
            MATCH (d:Device {id: $device_id})-[:HAS_SENSOR]->(s:Sensor)
            OPTIONAL MATCH (m:Measurement)-[:MEASURED_BY]->(s)
            WITH s, m ORDER BY m.timestamp DESC LIMIT 1
            RETURN s.sensor_type as sensor_type,
                   m.value as latest_value,
                   m.timestamp as latest_timestamp
        """, {"device_id": device_id})
        
        sensor_data = []
        while measurements_result.has_next():
            row = measurements_result.get_next()
            if row[1] is not None:  # 測定値が存在する場合
                sensor_data.append({
                    "sensor_type": row[0],
                    "latest_value": row[1],
                    "latest_timestamp": row[2]
                })
                
        return {
            "device": device_info,
            "sensors": sensor_data
        }
        
    def get_fleet_status(self) -> Dict[str, Any]:
        """全デバイスのステータスサマリー"""
        # デバイス統計
        device_stats = self.conn.execute("""
            MATCH (d:Device)
            RETURN COUNT(d) as total,
                   COUNT(CASE WHEN d.status = 'online' THEN 1 END) as online,
                   COUNT(CASE WHEN d.battery_level < 20 THEN 1 END) as low_battery
        """)
        
        stats = {"total": 0, "online": 0, "low_battery": 0}
        if device_stats.has_next():
            row = device_stats.get_next()
            stats = {
                "total": row[0],
                "online": row[1],
                "low_battery": row[2]
            }
            
        # アクティブアラート
        alert_stats = self.conn.execute("""
            MATCH (a:Alert)
            WHERE a.acknowledged = false
            RETURN a.severity as severity, COUNT(a) as count
        """)
        
        alerts = []
        while alert_stats.has_next():
            row = alert_stats.get_next()
            alerts.append({
                "severity": row[0],
                "count": row[1]
            })
            
        return {
            "devices": stats,
            "active_alerts": alerts
        }


@pytest.mark.asyncio
async def test_environmental_monitoring_network():
    """環境モニタリングネットワークのシナリオ"""
    
    print("\n=== 環境モニタリングネットワーク ===")
    
    # 複数の環境センサーデバイスを作成
    devices = [
        IoTDevice("env-sensor-01", "environmental", "Building A - Floor 1"),
        IoTDevice("env-sensor-02", "environmental", "Building A - Floor 2"),
        IoTDevice("env-sensor-03", "environmental", "Building B - Floor 1")
    ]
    
    # ゲートウェイを作成
    gateway = IoTGateway("gateway-main")
    
    # 各デバイスにセンサーを追加
    for device in devices:
        device.add_sensor("temperature", "°C", 15.0, 30.0)
        device.add_sensor("humidity", "%", 30.0, 70.0)
        device.add_sensor("co2", "ppm", 400.0, 1000.0)
    
    print("環境センサーネットワークを初期化")
    
    # === シナリオ1: 通常のデータ収集 ===
    print("\n=== シナリオ1: 定期データ収集 ===")
    
    for i in range(5):  # 5回の測定サイクル
        print(f"\n測定サイクル {i+1}:")
        
        for device in devices:
            # センサー値を生成（正常範囲内）
            temp = 20.0 + random.uniform(-2, 2)
            humidity = 50.0 + random.uniform(-10, 10)
            co2 = 600.0 + random.uniform(-100, 100)
            
            # 測定値を収集
            temp_meas = device.collect_measurement("temperature", temp)
            humid_meas = device.collect_measurement("humidity", humidity)
            co2_meas = device.collect_measurement("co2", co2)
            
            # ゲートウェイに同期
            for meas in [temp_meas, humid_meas, co2_meas]:
                gateway.conn.execute("""
                    CREATE (m:Measurement {
                        id: $id,
                        timestamp: $timestamp,
                        value: $value,
                        quality: $quality
                    })
                """, {
                    "id": meas["id"],
                    "timestamp": meas["timestamp"],
                    "value": meas["value"],
                    "quality": meas["quality"]
                })
            
            # バッテリー消費
            device.simulate_battery_drain()
            
            print(f"{device.location}: T={temp:.1f}°C, H={humidity:.1f}%, CO2={co2:.0f}ppm, Battery={device.battery_level:.1f}%")
        
        await asyncio.sleep(0.1)  # シミュレーション用の遅延
    
    # === シナリオ2: 異常値検出とアラート ===
    print("\n=== シナリオ2: 異常値検出 ===")
    
    # Building Aで温度異常を発生
    abnormal_temp = 35.0  # 閾値超過
    abnormal_co2 = 1500.0  # 危険レベル
    
    device_a = devices[0]
    temp_meas = device_a.collect_measurement("temperature", abnormal_temp)
    co2_meas = device_a.collect_measurement("co2", abnormal_co2)
    
    # 閾値チェック
    temp_alert = device_a.check_thresholds("temperature", abnormal_temp)
    co2_alert = device_a.check_thresholds("co2", abnormal_co2)
    
    if temp_alert:
        print(f"⚠️ 温度アラート: {temp_alert['message']}")
        
    if co2_alert:
        print(f"🚨 CO2アラート: {co2_alert['message']}")
    
    # === シナリオ3: デバイス障害とデータ品質 ===
    print("\n=== シナリオ3: デバイス障害シミュレーション ===")
    
    # デバイス2のバッテリーを低下させる
    devices[1].battery_level = 15.0
    low_battery_meas = devices[1].collect_measurement("temperature", 22.0)
    print(f"低バッテリーデバイスのデータ品質: {low_battery_meas['quality']}")
    
    # デバイス3をオフラインにする
    devices[2].is_online = False
    offline_meas = devices[2].collect_measurement("temperature", 21.0)
    print(f"オフラインデバイスのデータ品質: {offline_meas['quality']}")
    
    # === ゲートウェイでの集約分析 ===
    print("\n=== ゲートウェイ集約分析 ===")
    
    # フリート全体のステータス
    fleet_status = gateway.get_fleet_status()
    print(f"\nデバイスステータス:")
    print(f"- 総数: {fleet_status['devices']['total']}")
    print(f"- オンライン: {fleet_status['devices']['online']}")
    print(f"- 低バッテリー: {fleet_status['devices']['low_battery']}")
    
    print(f"\nアクティブアラート:")
    for alert in fleet_status['active_alerts']:
        print(f"- {alert['severity']}: {alert['count']}件")
    
    # 各デバイスのデータを集約
    for device in devices:
        agg_data = gateway.aggregate_device_data(device.device_id)
        if agg_data['device']:
            print(f"\n{device.location}:")
            print(f"  状態: {agg_data['device']['status']}, バッテリー: {agg_data['device']['battery_level']:.1f}%")
            for sensor in agg_data['sensors']:
                print(f"  {sensor['sensor_type']}: {sensor['latest_value']:.1f}")
    
    print("\n✅ 環境モニタリングシナリオ完了")


@pytest.mark.asyncio
async def test_industrial_iot_predictive_maintenance():
    """産業IoT予知保全シナリオ"""
    
    print("\n=== 産業IoT予知保全シナリオ ===")
    
    # 工場の機械設備をシミュレート
    machines = [
        IoTDevice("machine-cnc-01", "cnc_machine", "Production Line A"),
        IoTDevice("machine-pump-01", "pump", "Cooling System"),
        IoTDevice("machine-motor-01", "motor", "Conveyor Belt")
    ]
    
    gateway = IoTGateway("factory-gateway")
    
    # 機械ごとに異なるセンサーを設定
    # CNCマシン
    machines[0].add_sensor("spindle_speed", "rpm", 0, 10000)
    machines[0].add_sensor("vibration", "mm/s", 0, 10)
    machines[0].add_sensor("temperature", "°C", 20, 80)
    
    # ポンプ
    machines[1].add_sensor("flow_rate", "L/min", 50, 200)
    machines[1].add_sensor("pressure", "bar", 1, 10)
    machines[1].add_sensor("vibration", "mm/s", 0, 5)
    
    # モーター
    machines[2].add_sensor("current", "A", 0, 50)
    machines[2].add_sensor("temperature", "°C", 20, 90)
    machines[2].add_sensor("rpm", "rpm", 0, 3000)
    
    print("産業機器のセンサーネットワークを初期化")
    
    # ゲートウェイにもセンサー情報を同期
    for machine in machines:
        # デバイス情報を同期
        gateway.conn.execute("""
            MERGE (d:Device {id: $device_id})
            SET d.type = $type,
                d.location = $location,
                d.status = 'online',
                d.battery_level = $battery,
                d.last_seen = $timestamp
        """, {
            "device_id": machine.device_id,
            "type": machine.device_type,
            "location": machine.location,
            "battery": machine.battery_level,
            "timestamp": int(time.time() * 1000)
        })
        
        # センサー情報を同期
        sensor_configs = {
            "cnc_machine": [("spindle_speed", "rpm"), ("vibration", "mm/s"), ("temperature", "°C")],
            "pump": [("flow_rate", "L/min"), ("pressure", "bar"), ("vibration", "mm/s")],
            "motor": [("current", "A"), ("temperature", "°C"), ("rpm", "rpm")]
        }
        
        for sensor_type, unit in sensor_configs[machine.device_type]:
            sensor_id = f"sensor-{machine.device_id}-{sensor_type}"
            gateway.conn.execute("""
                MERGE (s:Sensor {id: $sensor_id})
                SET s.device_id = $device_id,
                    s.sensor_type = $sensor_type,
                    s.unit = $unit
            """, {
                "sensor_id": sensor_id,
                "device_id": machine.device_id,
                "sensor_type": sensor_type,
                "unit": unit
            })
            
            # リレーションシップも作成
            gateway.conn.execute("""
                MATCH (d:Device {id: $device_id})
                MATCH (s:Sensor {id: $sensor_id})
                MERGE (d)-[:HAS_SENSOR]->(s)
            """, {
                "device_id": machine.device_id,
                "sensor_id": sensor_id
            })
    
    # === シナリオ1: 正常運転データの収集 ===
    print("\n=== シナリオ1: 正常運転パターン ===")
    
    normal_patterns = {
        "cnc_machine": {
            "spindle_speed": 5000,
            "vibration": 2.0,
            "temperature": 45
        },
        "pump": {
            "flow_rate": 120,
            "pressure": 5,
            "vibration": 1.5
        },
        "motor": {
            "current": 25,
            "temperature": 50,
            "rpm": 1500
        }
    }
    
    for cycle in range(3):
        print(f"\n運転サイクル {cycle + 1}:")
        
        for machine in machines:
            pattern = normal_patterns[machine.device_type]
            measurements = []
            
            for sensor_type, base_value in pattern.items():
                # 正常範囲内での変動
                value = base_value * (1 + random.uniform(-0.05, 0.05))
                meas = machine.collect_measurement(sensor_type, value)
                measurements.append(meas)
                
                # ゲートウェイに同期
                gateway.sync_measurement(meas)
                
                # デバイス情報も同期
                gateway.conn.execute("""
                    MERGE (d:Device {id: $device_id})
                    SET d.type = $type,
                        d.location = $location,
                        d.status = 'online',
                        d.battery_level = $battery,
                        d.last_seen = $timestamp
                """, {
                    "device_id": machine.device_id,
                    "type": machine.device_type,
                    "location": machine.location,
                    "battery": machine.battery_level,
                    "timestamp": meas["timestamp"]
                })
            
            print(f"{machine.location}: 正常運転中")
        
        await asyncio.sleep(0.1)
    
    # === シナリオ2: 異常パターンの検出 ===
    print("\n=== シナリオ2: 異常パターン検出 ===")
    
    # CNCマシンで振動増加（ベアリング劣化の兆候）
    print("\nCNCマシンで振動異常を検出:")
    for i in range(5):
        # 振動が徐々に増加
        vibration = 2.0 + i * 1.5
        meas = machines[0].collect_measurement("vibration", vibration)
        alert = machines[0].check_thresholds("vibration", vibration)
        
        if alert:
            print(f"  サイクル{i+1}: 振動 {vibration:.1f}mm/s - {alert['severity']} アラート")
            
            # 関連する他のセンサー値も確認
            temp = 45 + i * 5  # 温度も上昇
            temp_meas = machines[0].collect_measurement("temperature", temp)
            print(f"    関連: 温度 {temp:.1f}°C")
    
    # === シナリオ3: 予知保全の推奨 ===
    print("\n=== シナリオ3: 予知保全分析 ===")
    
    # 各機械の最近のトレンドを分析
    for machine in machines:
        print(f"\n{machine.location}の状態分析:")
        
        # 振動センサーがある場合、トレンドを確認
        if machine.device_type in ["cnc_machine", "pump"]:
            recent_vibs = machine.get_recent_measurements("vibration", minutes=30)
            
            if len(recent_vibs) >= 2:
                # トレンド計算（簡易版）
                first_val = recent_vibs[-1]["value"]
                last_val = recent_vibs[0]["value"]
                trend = (last_val - first_val) / first_val * 100
                
                print(f"  振動トレンド: {trend:+.1f}%")
                
                if trend > 50:
                    print(f"  ⚠️ 推奨: 予防保全を検討（振動が急速に増加）")
                elif trend > 20:
                    print(f"  📊 注意: 継続的な監視が必要")
                else:
                    print(f"  ✅ 正常: 安定した運転状態")
    
    # === シナリオ4: クロスマシン相関分析 ===
    print("\n=== シナリオ4: システム全体の相関分析 ===")
    
    # ポンプの流量低下がモーターの負荷に影響
    print("\n冷却システムの連鎖影響シミュレーション:")
    
    # ポンプの流量低下
    low_flow = 70  # 正常値の約60%
    pump_meas = machines[1].collect_measurement("flow_rate", low_flow)
    pump_alert = machines[1].check_thresholds("flow_rate", low_flow)
    print(f"1. ポンプ流量低下: {low_flow}L/min")
    
    # モーターの温度上昇（冷却不足）
    high_temp = 85  # 警告レベル
    motor_meas = machines[2].collect_measurement("temperature", high_temp)
    motor_alert = machines[2].check_thresholds("temperature", high_temp)
    print(f"2. モーター温度上昇: {high_temp}°C")
    
    # CNCマシンへの影響
    cnc_temp = 75  # 通常より高い
    cnc_meas = machines[0].collect_measurement("temperature", cnc_temp)
    print(f"3. CNCマシン温度: {cnc_temp}°C")
    
    print("\n相関分析結果:")
    print("→ 冷却システムの問題が生産ライン全体に波及")
    print("→ 推奨アクション: 冷却システムの緊急点検")
    
    print("\n✅ 産業IoT予知保全シナリオ完了")


@pytest.mark.asyncio
async def test_smart_city_traffic_monitoring():
    """スマートシティ交通監視シナリオ"""
    
    print("\n=== スマートシティ交通監視シナリオ ===")
    
    # 交通センサーデバイスを作成
    traffic_sensors = [
        IoTDevice("traffic-int-01", "intersection", "Main St & 1st Ave"),
        IoTDevice("traffic-int-02", "intersection", "Main St & 5th Ave"),
        IoTDevice("traffic-hwy-01", "highway", "Highway 101 - Exit 23")
    ]
    
    gateway = IoTGateway("city-traffic-gateway")
    
    # センサーを追加
    for sensor in traffic_sensors:
        sensor.add_sensor("vehicle_count", "vehicles/min", 0, 100)
        sensor.add_sensor("avg_speed", "km/h", 0, 120)
        sensor.add_sensor("occupancy", "%", 0, 100)
        
        if sensor.device_type == "intersection":
            sensor.add_sensor("wait_time", "seconds", 0, 300)
    
    print("交通監視ネットワークを初期化")
    
    # === シナリオ1: 通常の交通フロー ===
    print("\n=== シナリオ1: 通常時の交通パターン ===")
    
    # 時間帯別の交通パターン
    time_patterns = [
        {"name": "早朝", "multiplier": 0.3},
        {"name": "朝ラッシュ", "multiplier": 1.5},
        {"name": "日中", "multiplier": 0.7},
        {"name": "夕方ラッシュ", "multiplier": 1.8},
        {"name": "夜間", "multiplier": 0.2}
    ]
    
    for pattern in time_patterns[:3]:  # 最初の3つの時間帯をシミュレート
        print(f"\n{pattern['name']}の交通状況:")
        
        for sensor in traffic_sensors:
            # 基準値に時間帯係数を適用
            base_count = 30 if sensor.device_type == "intersection" else 50
            vehicle_count = base_count * pattern['multiplier'] + random.randint(-5, 5)
            
            base_speed = 40 if sensor.device_type == "intersection" else 80
            avg_speed = base_speed / (0.5 + pattern['multiplier'])
            
            occupancy = min(95, vehicle_count * 1.5)
            
            # 測定値を収集
            count_meas = sensor.collect_measurement("vehicle_count", vehicle_count)
            speed_meas = sensor.collect_measurement("avg_speed", avg_speed)
            occ_meas = sensor.collect_measurement("occupancy", occupancy)
            
            # ゲートウェイに同期
            for meas in [count_meas, speed_meas, occ_meas]:
                gateway.sync_measurement(meas)
                
            # デバイス情報も同期
            gateway.conn.execute("""
                MERGE (d:Device {id: $device_id})
                SET d.type = $type,
                    d.location = $location,
                    d.status = 'online',
                    d.battery_level = $battery,
                    d.last_seen = $timestamp
            """, {
                "device_id": sensor.device_id,
                "type": sensor.device_type,
                "location": sensor.location,
                "battery": sensor.battery_level,
                "timestamp": count_meas["timestamp"]
            })
            
            # センサー情報も同期
            for sensor_type_name in ["vehicle_count", "avg_speed", "occupancy"]:
                sensor_id = f"sensor-{sensor.device_id}-{sensor_type_name}"
                gateway.conn.execute("""
                    MERGE (s:Sensor {id: $sensor_id})
                    SET s.device_id = $device_id,
                        s.sensor_type = $sensor_type
                """, {
                    "sensor_id": sensor_id,
                    "device_id": sensor.device_id,
                    "sensor_type": sensor_type_name
                })
                
                # リレーションシップも作成
                gateway.conn.execute("""
                    MATCH (d:Device {id: $device_id})
                    MATCH (s:Sensor {id: $sensor_id})
                    MERGE (d)-[:HAS_SENSOR]->(s)
                """, {
                    "device_id": sensor.device_id,
                    "sensor_id": sensor_id
                })
            
            # 交差点の場合は待ち時間も
            if sensor.device_type == "intersection":
                wait_time = occupancy * 2  # 占有率に比例
                wait_meas = sensor.collect_measurement("wait_time", wait_time)
                gateway.sync_measurement(wait_meas)
                
                # 待ち時間センサーも同期
                wait_sensor_id = f"sensor-{sensor.device_id}-wait_time"
                gateway.conn.execute("""
                    MERGE (s:Sensor {id: $sensor_id})
                    SET s.device_id = $device_id,
                        s.sensor_type = 'wait_time'
                """, {
                    "sensor_id": wait_sensor_id,
                    "device_id": sensor.device_id
                })
                
                gateway.conn.execute("""
                    MATCH (d:Device {id: $device_id})
                    MATCH (s:Sensor {id: $sensor_id})
                    MERGE (d)-[:HAS_SENSOR]->(s)
                """, {
                    "device_id": sensor.device_id,
                    "sensor_id": wait_sensor_id
                })
                
            print(f"  {sensor.location}: {vehicle_count:.0f}台/分, {avg_speed:.0f}km/h, 占有率{occupancy:.0f}%")
    
    # === シナリオ2: 交通事故による渋滞 ===
    print("\n=== シナリオ2: 事故による渋滞発生 ===")
    
    accident_location = traffic_sensors[0]  # Main St & 1st Ave
    print(f"\n事故発生: {accident_location.location}")
    
    # 事故地点の交通パラメータ
    accident_params = {
        "vehicle_count": 5,  # 大幅に減少
        "avg_speed": 10,     # ほぼ停止
        "occupancy": 95,     # 満杯
        "wait_time": 600     # 10分待ち
    }
    
    for param, value in accident_params.items():
        if param == "wait_time" and accident_location.device_type != "intersection":
            continue
        meas = accident_location.collect_measurement(param, value)
        alert = accident_location.check_thresholds(param, value)
        if alert:
            print(f"  🚨 {param}: {value} - {alert['severity']}アラート")
    
    # 周辺への影響をシミュレート
    print("\n周辺交差点への波及効果:")
    
    # 5th Aveにも影響
    spillover_sensor = traffic_sensors[1]
    spillover_meas = spillover_sensor.collect_measurement("vehicle_count", 60)
    spillover_speed = spillover_sensor.collect_measurement("avg_speed", 25)
    print(f"  {spillover_sensor.location}: 交通量増加、速度低下")
    
    # === シナリオ3: 動的な交通制御 ===
    print("\n=== シナリオ3: 適応的信号制御 ===")
    
    # 各交差点の現在の状況を分析
    for sensor in traffic_sensors:
        if sensor.device_type == "intersection":
            recent_counts = sensor.get_recent_measurements("vehicle_count", minutes=15)
            recent_waits = sensor.get_recent_measurements("wait_time", minutes=15)
            
            if recent_counts and recent_waits:
                avg_count = sum(m["value"] for m in recent_counts) / len(recent_counts)
                avg_wait = sum(m["value"] for m in recent_waits) / len(recent_waits)
                
                print(f"\n{sensor.location}:")
                print(f"  平均交通量: {avg_count:.0f}台/分")
                print(f"  平均待ち時間: {avg_wait:.0f}秒")
                
                # 信号制御の推奨
                if avg_wait > 120:
                    print(f"  → 推奨: 青信号時間を延長")
                elif avg_wait < 30 and avg_count < 20:
                    print(f"  → 推奨: 青信号時間を短縮")
                else:
                    print(f"  → 現在の設定を維持")
    
    # === ゲートウェイでの統合分析 ===
    print("\n=== 都市全体の交通状況 ===")
    
    # ネットワーク全体の統計
    result = gateway.conn.execute("""
        MATCH (m:Measurement)-[:MEASURED_BY]->(s:Sensor {sensor_type: 'vehicle_count'})
        WHERE m.timestamp > $cutoff
        RETURN AVG(m.value) as avg_flow,
               MAX(m.value) as max_flow,
               MIN(m.value) as min_flow
    """, {"cutoff": int((time.time() - 3600) * 1000)})
    
    if result.has_next():
        row = result.get_next()
        print(f"\n過去1時間の交通流量統計:")
        if row[0] is not None:
            print(f"  平均: {row[0]:.0f}台/分")
            print(f"  最大: {row[1]:.0f}台/分")
            print(f"  最小: {row[2]:.0f}台/分")
        else:
            print("  データが不足しています")
    
    print("\n✅ スマートシティ交通監視シナリオ完了")


if __name__ == "__main__":
    # IoTデータ収集のE2Eテストを実行
    asyncio.run(test_environmental_monitoring_network())
    asyncio.run(test_industrial_iot_predictive_maintenance())
    asyncio.run(test_smart_city_traffic_monitoring())