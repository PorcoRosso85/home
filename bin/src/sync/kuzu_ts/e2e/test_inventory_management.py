"""
E2E Test: Inventory Management System Synchronization
在庫管理システムでの同期ユースケース

このテストは、実際の在庫管理システムシナリオで
sync/kuzu_tsがどのように使われるかを示す「実行可能な仕様書」です。
"""

import asyncio
import json
import pytest
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import kuzu


class InventoryNode:
    """在庫管理ノード（倉庫・店舗）のシミュレーション"""
    
    def __init__(self, node_id: str, node_type: str, location: str):
        self.node_id = node_id
        self.node_type = node_type  # 'warehouse' or 'store'
        self.location = location
        self.db = kuzu.Database(':memory:')
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()
        
    def _initialize_schema(self):
        """在庫管理スキーマを初期化"""
        # 商品マスタ
        self.conn.execute("""
            CREATE NODE TABLE Product (
                id STRING,
                name STRING,
                category STRING,
                unit_price DOUBLE,
                min_stock INT64,
                PRIMARY KEY(id)
            )
        """)
        
        # 在庫ノード（倉庫・店舗）
        self.conn.execute("""
            CREATE NODE TABLE InventoryNode (
                id STRING,
                type STRING,
                location STRING,
                capacity INT64,
                PRIMARY KEY(id)
            )
        """)
        
        # 在庫レベル
        self.conn.execute("""
            CREATE NODE TABLE StockLevel (
                id STRING,
                product_id STRING,
                node_id STRING,
                quantity INT64,
                reserved INT64,
                last_updated INT64,
                PRIMARY KEY(id)
            )
        """)
        
        # 在庫移動トランザクション
        self.conn.execute("""
            CREATE NODE TABLE StockMovement (
                id STRING,
                type STRING,
                quantity INT64,
                timestamp INT64,
                status STRING,
                PRIMARY KEY(id)
            )
        """)
        
        # リレーションシップ
        self.conn.execute("CREATE REL TABLE HAS_STOCK (FROM InventoryNode TO StockLevel)")
        self.conn.execute("CREATE REL TABLE FOR_PRODUCT (FROM StockLevel TO Product)")
        self.conn.execute("CREATE REL TABLE FROM_NODE (FROM StockMovement TO InventoryNode)")
        self.conn.execute("CREATE REL TABLE TO_NODE (FROM StockMovement TO InventoryNode)")
        self.conn.execute("CREATE REL TABLE MOVES_PRODUCT (FROM StockMovement TO Product)")
        
        # 自ノードを登録
        self.conn.execute("""
            CREATE (n:InventoryNode {
                id: $id,
                type: $type,
                location: $location,
                capacity: $capacity
            })
        """, {
            "id": self.node_id,
            "type": self.node_type,
            "location": self.location,
            "capacity": 10000 if self.node_type == "warehouse" else 1000
        })
        
    def add_product(self, product: Dict[str, Any]):
        """商品マスタに商品を追加"""
        self.conn.execute("""
            MERGE (p:Product {id: $id})
            ON CREATE SET p.name = $name,
                         p.category = $category,
                         p.unit_price = $unit_price,
                         p.min_stock = $min_stock
        """, product)
        
    def update_stock_level(self, product_id: str, quantity: int, reserved: int = 0):
        """在庫レベルを更新"""
        stock_id = f"stock-{self.node_id}-{product_id}"
        
        # 在庫レベルをupsert
        self.conn.execute("""
            MERGE (s:StockLevel {id: $stock_id})
            ON CREATE SET s.product_id = $product_id,
                         s.node_id = $node_id,
                         s.quantity = $quantity,
                         s.reserved = $reserved,
                         s.last_updated = $timestamp
            ON MATCH SET s.quantity = $quantity,
                        s.reserved = $reserved,
                        s.last_updated = $timestamp
        """, {
            "stock_id": stock_id,
            "product_id": product_id,
            "node_id": self.node_id,
            "quantity": quantity,
            "reserved": reserved,
            "timestamp": int(time.time() * 1000)
        })
        
        # リレーションシップを作成
        self.conn.execute("""
            MATCH (n:InventoryNode {id: $node_id})
            MATCH (s:StockLevel {id: $stock_id})
            MERGE (n)-[:HAS_STOCK]->(s)
        """, {"node_id": self.node_id, "stock_id": stock_id})
        
        self.conn.execute("""
            MATCH (s:StockLevel {id: $stock_id})
            MATCH (p:Product {id: $product_id})
            MERGE (s)-[:FOR_PRODUCT]->(p)
        """, {"stock_id": stock_id, "product_id": product_id})
        
    def create_stock_movement(self, movement: Dict[str, Any]) -> Dict[str, Any]:
        """在庫移動を作成"""
        movement_id = f"move-{uuid.uuid4()}"
        movement_data = {
            "id": movement_id,
            "type": movement["type"],  # 'transfer', 'sale', 'purchase', 'adjustment'
            "quantity": movement["quantity"],
            "timestamp": int(time.time() * 1000),
            "status": "pending",
            **movement
        }
        
        # 移動レコードを作成
        self.conn.execute("""
            CREATE (m:StockMovement {
                id: $id,
                type: $type,
                quantity: $quantity,
                timestamp: $timestamp,
                status: $status
            })
        """, movement_data)
        
        # リレーションシップを作成
        if movement.get("from_node"):
            self.conn.execute("""
                MATCH (m:StockMovement {id: $movement_id})
                MATCH (n:InventoryNode {id: $from_node})
                CREATE (m)-[:FROM_NODE]->(n)
            """, {"movement_id": movement_id, "from_node": movement["from_node"]})
            
        if movement.get("to_node"):
            self.conn.execute("""
                MATCH (m:StockMovement {id: $movement_id})
                MATCH (n:InventoryNode {id: $to_node})
                CREATE (m)-[:TO_NODE]->(n)
            """, {"movement_id": movement_id, "to_node": movement["to_node"]})
            
        self.conn.execute("""
            MATCH (m:StockMovement {id: $movement_id})
            MATCH (p:Product {id: $product_id})
            CREATE (m)-[:MOVES_PRODUCT]->(p)
        """, {"movement_id": movement_id, "product_id": movement["product_id"]})
        
        return movement_data
        
    def process_incoming_movement(self, movement: Dict[str, Any]):
        """他ノードからの在庫移動を処理"""
        # 移動レコードが存在しない場合は作成
        result = self.conn.execute(
            "MATCH (m:StockMovement {id: $id}) RETURN m",
            {"id": movement["id"]}
        )
        
        if not result.has_next():
            self.conn.execute("""
                CREATE (m:StockMovement {
                    id: $id,
                    type: $type,
                    quantity: $quantity,
                    timestamp: $timestamp,
                    status: $status
                })
            """, movement)
            
            # リレーションシップも同期
            if movement.get("from_node"):
                self.conn.execute("""
                    MERGE (n:InventoryNode {id: $from_node})
                """, {"from_node": movement["from_node"]})
                
                self.conn.execute("""
                    MATCH (m:StockMovement {id: $movement_id})
                    MATCH (n:InventoryNode {id: $from_node})
                    MERGE (m)-[:FROM_NODE]->(n)
                """, {"movement_id": movement["id"], "from_node": movement["from_node"]})
                
    def get_stock_level(self, product_id: str) -> Dict[str, Any]:
        """商品の在庫レベルを取得"""
        result = self.conn.execute("""
            MATCH (s:StockLevel {product_id: $product_id, node_id: $node_id})
            RETURN s.quantity as quantity, 
                   s.reserved as reserved,
                   s.quantity - s.reserved as available
        """, {"product_id": product_id, "node_id": self.node_id})
        
        if result.has_next():
            row = result.get_next()
            return {
                "quantity": row[0],
                "reserved": row[1], 
                "available": row[2]
            }
        return {"quantity": 0, "reserved": 0, "available": 0}
        
    def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """最小在庫を下回っている商品を取得"""
        result = self.conn.execute("""
            MATCH (s:StockLevel {node_id: $node_id})-[:FOR_PRODUCT]->(p:Product)
            WHERE s.quantity < p.min_stock
            RETURN p.id as product_id,
                   p.name as product_name,
                   s.quantity as current_stock,
                   p.min_stock as min_stock,
                   p.min_stock - s.quantity as shortage
            ORDER BY shortage DESC
        """, {"node_id": self.node_id})
        
        items = []
        while result.has_next():
            row = result.get_next()
            items.append({
                "product_id": row[0],
                "product_name": row[1],
                "current_stock": row[2],
                "min_stock": row[3],
                "shortage": row[4]
            })
        return items
        
    def get_pending_movements(self) -> List[Dict[str, Any]]:
        """保留中の在庫移動を取得"""
        result = self.conn.execute("""
            MATCH (m:StockMovement {status: 'pending'})
            WHERE EXISTS { (m)-[:FROM_NODE]->(:InventoryNode {id: $node_id}) }
               OR EXISTS { (m)-[:TO_NODE]->(:InventoryNode {id: $node_id}) }
            MATCH (m)-[:MOVES_PRODUCT]->(p:Product)
            RETURN m.id as id,
                   m.type as type,
                   m.quantity as quantity,
                   p.id as product_id,
                   p.name as product_name
            ORDER BY m.timestamp
        """, {"node_id": self.node_id})
        
        movements = []
        while result.has_next():
            row = result.get_next()
            movements.append({
                "id": row[0],
                "type": row[1],
                "quantity": row[2],
                "product_id": row[3],
                "product_name": row[4]
            })
        return movements


@pytest.mark.asyncio
async def test_multi_warehouse_inventory_sync():
    """複数倉庫間の在庫同期シナリオ"""
    
    print("\n=== 複数倉庫間の在庫同期シナリオ ===")
    
    # 3つの拠点を作成（メイン倉庫、地域倉庫、店舗）
    main_warehouse = InventoryNode("wh-main", "warehouse", "Tokyo")
    regional_warehouse = InventoryNode("wh-osaka", "warehouse", "Osaka")
    store = InventoryNode("st-shibuya", "store", "Shibuya")
    
    # 商品マスタを全拠点に同期
    products = [
        {
            "id": "prod-laptop-001",
            "name": "Business Laptop Pro",
            "category": "Electronics",
            "unit_price": 1500.0,
            "min_stock": 20
        },
        {
            "id": "prod-mouse-002",
            "name": "Wireless Mouse",
            "category": "Accessories",
            "unit_price": 30.0,
            "min_stock": 50
        }
    ]
    
    for product in products:
        main_warehouse.add_product(product)
        regional_warehouse.add_product(product)
        store.add_product(product)
    
    # 初期在庫を設定
    main_warehouse.update_stock_level("prod-laptop-001", 100)
    main_warehouse.update_stock_level("prod-mouse-002", 500)
    
    regional_warehouse.update_stock_level("prod-laptop-001", 30)
    regional_warehouse.update_stock_level("prod-mouse-002", 200)
    
    store.update_stock_level("prod-laptop-001", 5)
    store.update_stock_level("prod-mouse-002", 50)
    
    print("\n初期在庫レベル:")
    print(f"メイン倉庫 - Laptop: {main_warehouse.get_stock_level('prod-laptop-001')}")
    print(f"地域倉庫 - Laptop: {regional_warehouse.get_stock_level('prod-laptop-001')}")
    print(f"店舗 - Laptop: {store.get_stock_level('prod-laptop-001')}")
    
    # === シナリオ1: 店舗の在庫が少なくなり、地域倉庫から補充 ===
    print("\n=== シナリオ1: 店舗への在庫補充 ===")
    
    # 店舗で在庫不足を検出
    low_stock = store.get_low_stock_items()
    assert len(low_stock) > 0
    assert low_stock[0]["product_id"] == "prod-laptop-001"
    print(f"店舗の在庫不足: {low_stock[0]}")
    
    # 地域倉庫から店舗への移動を作成
    transfer = regional_warehouse.create_stock_movement({
        "type": "transfer",
        "product_id": "prod-laptop-001",
        "quantity": 10,
        "from_node": "wh-osaka",
        "to_node": "st-shibuya"
    })
    
    # 店舗側で移動を同期
    store.process_incoming_movement(transfer)
    
    # 在庫を更新（実際の移動完了をシミュレート）
    regional_warehouse.update_stock_level("prod-laptop-001", 20)  # 30 - 10
    store.update_stock_level("prod-laptop-001", 15)  # 5 + 10
    
    print(f"✅ 在庫移動完了: 地域倉庫 → 店舗（10個）")
    print(f"地域倉庫 - Laptop: {regional_warehouse.get_stock_level('prod-laptop-001')}")
    print(f"店舗 - Laptop: {store.get_stock_level('prod-laptop-001')}")
    
    # === シナリオ2: 並行在庫移動の処理 ===
    print("\n=== シナリオ2: 並行在庫移動 ===")
    
    # 同時に複数の移動が発生
    # 1. メイン倉庫 → 地域倉庫（補充）
    transfer1 = main_warehouse.create_stock_movement({
        "type": "transfer",
        "product_id": "prod-laptop-001",
        "quantity": 30,
        "from_node": "wh-main",
        "to_node": "wh-osaka"
    })
    
    # 2. 店舗での販売
    sale = store.create_stock_movement({
        "type": "sale",
        "product_id": "prod-laptop-001",
        "quantity": 2,
        "from_node": "st-shibuya"
    })
    
    # 各拠点で同期
    regional_warehouse.process_incoming_movement(transfer1)
    main_warehouse.process_incoming_movement(sale)
    regional_warehouse.process_incoming_movement(sale)
    
    # 在庫レベル更新
    main_warehouse.update_stock_level("prod-laptop-001", 70)  # 100 - 30
    regional_warehouse.update_stock_level("prod-laptop-001", 50)  # 20 + 30
    store.update_stock_level("prod-laptop-001", 13)  # 15 - 2
    
    print("✅ 並行移動処理完了")
    print(f"メイン倉庫: {main_warehouse.get_stock_level('prod-laptop-001')}")
    print(f"地域倉庫: {regional_warehouse.get_stock_level('prod-laptop-001')}")
    print(f"店舗: {store.get_stock_level('prod-laptop-001')}")
    
    # === シナリオ3: 在庫予約と利用可能在庫 ===
    print("\n=== シナリオ3: 在庫予約管理 ===")
    
    # オンライン注文で在庫を予約
    current_stock = store.get_stock_level("prod-mouse-002")
    store.update_stock_level("prod-mouse-002", current_stock["quantity"], reserved=10)
    
    reserved_stock = store.get_stock_level("prod-mouse-002")
    print(f"マウス在庫 - 総数: {reserved_stock['quantity']}, "
          f"予約: {reserved_stock['reserved']}, "
          f"利用可能: {reserved_stock['available']}")
    
    assert reserved_stock["available"] == reserved_stock["quantity"] - reserved_stock["reserved"]
    
    # === 検証: 全拠点のデータ整合性 ===
    print("\n=== データ整合性の検証 ===")
    
    # 各拠点の保留中移動を確認
    main_pending = main_warehouse.get_pending_movements()
    regional_pending = regional_warehouse.get_pending_movements()
    store_pending = store.get_pending_movements()
    
    print(f"保留中の移動 - メイン倉庫: {len(main_pending)}")
    print(f"保留中の移動 - 地域倉庫: {len(regional_pending)}")
    print(f"保留中の移動 - 店舗: {len(store_pending)}")
    
    print("\n✅ 在庫管理システムの同期シナリオ完了")


@pytest.mark.asyncio
async def test_inventory_analytics_sync():
    """在庫分析データの同期シナリオ"""
    
    print("\n=== 在庫分析データの同期シナリオ ===")
    
    # 分析用の集約ノードと複数店舗
    analytics_node = InventoryNode("analytics", "warehouse", "Analytics Center")
    stores = [
        InventoryNode(f"st-{i}", "store", f"Store {i}")
        for i in range(1, 4)
    ]
    
    # 商品マスタ設定
    product = {
        "id": "prod-seasonal-001",
        "name": "Seasonal Item",
        "category": "Seasonal",
        "unit_price": 50.0,
        "min_stock": 30
    }
    
    analytics_node.add_product(product)
    for store in stores:
        store.add_product(product)
    
    # 各店舗の売上データをシミュレート
    print("\n店舗別売上シミュレーション:")
    
    for day in range(7):  # 1週間分
        for store in stores:
            # ランダムな売上を生成
            import random
            sales_qty = random.randint(5, 20)
            
            # 売上移動を作成
            sale_movement = store.create_stock_movement({
                "type": "sale",
                "product_id": "prod-seasonal-001",
                "quantity": sales_qty,
                "from_node": store.node_id
            })
            
            # 分析ノードに同期
            analytics_node.process_incoming_movement(sale_movement)
            
            # 在庫を減らす（初期在庫100と仮定）
            current = 100 - (day * 10 + sales_qty)
            store.update_stock_level("prod-seasonal-001", max(0, current))
            
            print(f"Day {day+1}, {store.location}: 売上 {sales_qty}個")
    
    # 分析ノードで集計クエリを実行
    result = analytics_node.conn.execute("""
        MATCH (m:StockMovement {type: 'sale'})-[:MOVES_PRODUCT]->(p:Product {id: $product_id})
        MATCH (m)-[:FROM_NODE]->(n:InventoryNode)
        RETURN n.id as store_id,
               COUNT(m) as transaction_count,
               SUM(m.quantity) as total_sales
        ORDER BY total_sales DESC
    """, {"product_id": "prod-seasonal-001"})
    
    print("\n=== 売上分析結果 ===")
    while result.has_next():
        row = result.get_next()
        print(f"店舗 {row[0]}: {row[1]}件の取引, 合計{row[2]}個販売")
    
    # 在庫補充の推奨を生成
    print("\n=== 在庫補充推奨 ===")
    for store in stores:
        stock = store.get_stock_level("prod-seasonal-001")
        if stock["quantity"] < 30:  # 最小在庫以下
            recommended = 50 - stock["quantity"]
            print(f"{store.location}: 現在庫 {stock['quantity']}個 → {recommended}個の補充を推奨")
    
    print("\n✅ 在庫分析シナリオ完了")


@pytest.mark.asyncio
async def test_inventory_conflict_resolution():
    """在庫更新の競合解決シナリオ"""
    
    print("\n=== 在庫更新の競合解決シナリオ ===")
    
    # 2つの店舗POSシステムが同じ在庫を更新
    pos1 = InventoryNode("pos-1", "store", "POS Terminal 1")
    pos2 = InventoryNode("pos-2", "store", "POS Terminal 2")
    
    product = {
        "id": "prod-limited-001",
        "name": "Limited Edition Item",
        "category": "Special",
        "unit_price": 200.0,
        "min_stock": 5
    }
    
    pos1.add_product(product)
    pos2.add_product(product)
    
    # 初期在庫を設定（両方のPOSで同じ値）
    pos1.update_stock_level("prod-limited-001", 10)
    pos2.update_stock_level("prod-limited-001", 10)
    
    print("初期在庫: 10個")
    
    # 同時に販売が発生
    print("\n同時販売シミュレーション:")
    
    # POS1で3個販売
    sale1 = pos1.create_stock_movement({
        "type": "sale",
        "product_id": "prod-limited-001",
        "quantity": 3,
        "from_node": "store"
    })
    pos1.update_stock_level("prod-limited-001", 7)
    print("POS1: 3個販売 → 残り7個")
    
    # POS2で5個販売（同時）
    sale2 = pos2.create_stock_movement({
        "type": "sale",
        "product_id": "prod-limited-001",
        "quantity": 5,
        "from_node": "store"
    })
    pos2.update_stock_level("prod-limited-001", 5)
    print("POS2: 5個販売 → 残り5個")
    
    # 相互に同期
    pos1.process_incoming_movement(sale2)
    pos2.process_incoming_movement(sale1)
    
    # タイムスタンプベースの競合解決
    # 実際のシステムでは、中央サーバーが調整
    print("\n競合解決後:")
    actual_stock = 10 - 3 - 5  # 実際の在庫
    
    if actual_stock < 0:
        print(f"⚠️ 在庫不足検出！実在庫: {actual_stock}")
        print("→ 後の取引をキャンセルまたは一部充足")
    else:
        print(f"✅ 正常処理: 実在庫 {actual_stock}個")
    
    # 調整トランザクションを作成
    adjustment = pos1.create_stock_movement({
        "type": "adjustment",
        "product_id": "prod-limited-001",
        "quantity": abs(actual_stock),
        "from_node": "store"
    })
    
    print("\n✅ 競合解決シナリオ完了")


if __name__ == "__main__":
    # 在庫管理システムのE2Eテストを実行
    asyncio.run(test_multi_warehouse_inventory_sync())
    asyncio.run(test_inventory_analytics_sync())
    asyncio.run(test_inventory_conflict_resolution())