"""
Priority Manager - Application Layer Implementation
優先順位管理のアプリケーション層実装
"""
import kuzu
from typing import List, Dict, Tuple, Optional


class PriorityManager:
    """Manages requirement priorities without UDF"""
    
    def __init__(self, conn: kuzu.Connection):
        self.conn = conn
    
    def redistribute_priorities(self) -> List[Dict]:
        """Redistribute all priorities evenly across 0-255 range"""
        # Get all requirements ordered by current priority
        result = self.conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.id, r.priority
            ORDER BY r.priority, r.id
        """)
        
        requirements = []
        while result.has_next():
            row = result.get_next()
            requirements.append({
                'id': row[0],
                'priority': row[1]
            })
        
        # Calculate new priorities
        total = len(requirements)
        if total == 0:
            return []
        
        # Begin transaction for atomic update
        self.conn.execute("BEGIN TRANSACTION")
        try:
            for i, req in enumerate(requirements):
                new_priority = int(255 * i / (total - 1)) if total > 1 else 128
                self.conn.execute(f"""
                    MATCH (r:RequirementEntity {{id: '{req['id']}'}})
                    SET r.priority = {new_priority}
                """)
                req['new_priority'] = new_priority
            
            self.conn.execute("COMMIT")
            return requirements
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e
    
    def compress_priorities(self, factor: float) -> List[Dict]:
        """Compress all priorities by a factor"""
        if factor <= 0 or factor >= 1:
            raise ValueError("Compression factor must be between 0 and 1")
        
        result = self.conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.id, r.priority
        """)
        
        updates = []
        while result.has_next():
            row = result.get_next()
            new_priority = int(row[1] * factor)
            updates.append((row[0], new_priority))
        
        # Apply updates
        self.conn.execute("BEGIN TRANSACTION")
        try:
            for req_id, new_priority in updates:
                self.conn.execute(f"""
                    MATCH (r:RequirementEntity {{id: '{req_id}'}})
                    SET r.priority = {new_priority}
                """)
            self.conn.execute("COMMIT")
            return [{'id': id, 'compressed_priority': p} for id, p in updates]
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e
    
    def normalize_priorities(self, min_val: int = 0, max_val: int = 255) -> List[Dict]:
        """Normalize priorities to specified range"""
        # Get current min and max
        result = self.conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN min(r.priority) AS min_p, max(r.priority) AS max_p
        """)
        row = result.get_next()
        current_min, current_max = row[0], row[1]
        
        if current_min == current_max:
            # All same priority - set to middle
            mid_val = (min_val + max_val) // 2
            self.conn.execute(f"""
                MATCH (r:RequirementEntity)
                SET r.priority = {mid_val}
            """)
            return []
        
        # Get all requirements and normalize
        result = self.conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.id, r.priority
        """)
        
        updates = []
        while result.has_next():
            row = result.get_next()
            req_id, current_priority = row[0], row[1]
            
            # Linear normalization
            normalized = min_val + ((current_priority - current_min) * (max_val - min_val)) // (current_max - current_min)
            updates.append((req_id, int(normalized)))
        
        # Apply updates
        self.conn.execute("BEGIN TRANSACTION")
        try:
            for req_id, new_priority in updates:
                self.conn.execute(f"""
                    MATCH (r:RequirementEntity {{id: '{req_id}'}})
                    SET r.priority = {new_priority}
                """)
            self.conn.execute("COMMIT")
            return [{'id': id, 'normalized_priority': p} for id, p in updates]
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e
    
    def find_priority_gap(self, target_priority: int) -> int:
        """Find optimal position for inserting a priority"""
        result = self.conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.priority
            ORDER BY r.priority
        """)
        
        priorities = []
        while result.has_next():
            priorities.append(result.get_next()[0])
        
        if not priorities:
            return target_priority
        
        # If target is at edges
        if target_priority <= priorities[0]:
            return max(0, target_priority)
        if target_priority >= priorities[-1]:
            return min(255, target_priority)
        
        # Find if target fits in a gap
        for i in range(len(priorities) - 1):
            if priorities[i] < target_priority < priorities[i + 1]:
                return target_priority
        
        # Find largest gap
        best_gap_size = 0
        best_position = target_priority
        
        for i in range(len(priorities) - 1):
            gap_size = priorities[i + 1] - priorities[i]
            if gap_size > best_gap_size:
                best_gap_size = gap_size
                best_position = (priorities[i] + priorities[i + 1]) // 2
        
        return best_position
    
    def resolve_priority_collision(self, req_id: str, desired_priority: int) -> int:
        """Resolve collision by finding next available priority"""
        # Check if priority is taken
        result = self.conn.execute(f"""
            MATCH (r:RequirementEntity)
            WHERE r.priority = {desired_priority} AND r.id <> '{req_id}'
            RETURN count(r) > 0 AS collision_exists
        """)
        
        if not result.get_next()[0]:
            return desired_priority  # No collision
        
        # Find nearest available priority
        for offset in range(1, 256):
            for direction in [1, -1]:
                candidate = desired_priority + (offset * direction)
                if 0 <= candidate <= 255:
                    result = self.conn.execute(f"""
                        MATCH (r:RequirementEntity)
                        WHERE r.priority = {candidate}
                        RETURN count(r) AS count
                    """)
                    if result.get_next()[0] == 0:
                        return candidate
        
        # If all priorities are taken, trigger redistribution
        self.redistribute_priorities()
        return desired_priority
    
    def handle_max_priority_conflict(self, new_req_id: str) -> None:
        """Handle multiple items claiming max priority"""
        # Count existing max priority items
        result = self.conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.priority = 255
            RETURN count(r) AS max_count, collect(r.id) AS max_ids
        """)
        row = result.get_next()
        max_count = row[0]
        max_ids = row[1]
        
        if max_count == 0:
            return  # No conflict
        
        # Strategy: Cascade down existing max priorities
        self.conn.execute("BEGIN TRANSACTION")
        try:
            # Move existing max priorities down
            for i, req_id in enumerate(max_ids):
                if req_id != new_req_id:
                    new_priority = 255 - (i + 1)
                    self.conn.execute(f"""
                        MATCH (r:RequirementEntity {{id: '{req_id}'}})
                        SET r.priority = {new_priority}
                    """)
            
            # Ensure new requirement gets 255
            self.conn.execute(f"""
                MATCH (r:RequirementEntity {{id: '{new_req_id}'}})
                SET r.priority = 255
            """)
            
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e
    
    def auto_cascade_priorities(self, start_priority: int = 250) -> None:
        """Automatically cascade priorities down from a starting point"""
        # Get all requirements at or above start_priority
        result = self.conn.execute(f"""
            MATCH (r:RequirementEntity)
            WHERE r.priority >= {start_priority}
            RETURN r.id, r.priority
            ORDER BY r.priority DESC, r.id
        """)
        
        high_priority_items = []
        while result.has_next():
            row = result.get_next()
            high_priority_items.append({'id': row[0], 'priority': row[1]})
        
        if not high_priority_items:
            return
        
        # Redistribute within the high priority range
        self.conn.execute("BEGIN TRANSACTION")
        try:
            total = len(high_priority_items)
            range_size = 255 - start_priority + 1
            
            for i, item in enumerate(high_priority_items):
                # Distribute evenly in the high priority range
                new_priority = 255 - int(i * range_size / total)
                self.conn.execute(f"""
                    MATCH (r:RequirementEntity {{id: '{item['id']}'}})
                    SET r.priority = {new_priority}
                """)
            
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e
    
    def smart_priority_rebalance(self, min_priority: int = 0, max_priority: int = 255) -> None:
        """Smart rebalancing within a specific range"""
        # Get requirements in range
        result = self.conn.execute(f"""
            MATCH (r:RequirementEntity)
            WHERE r.priority >= {min_priority} AND r.priority <= {max_priority}
            RETURN r.id, r.priority
            ORDER BY r.priority, r.id
        """)
        
        requirements_in_range = []
        while result.has_next():
            row = result.get_next()
            requirements_in_range.append({'id': row[0], 'priority': row[1]})
        
        if len(requirements_in_range) <= 1:
            return
        
        # Redistribute within range
        self.conn.execute("BEGIN TRANSACTION")
        try:
            total = len(requirements_in_range)
            range_size = max_priority - min_priority
            
            for i, req in enumerate(requirements_in_range):
                new_priority = min_priority + int(i * range_size / (total - 1))
                self.conn.execute(f"""
                    MATCH (r:RequirementEntity {{id: '{req['id']}'}})
                    SET r.priority = {new_priority}
                """)
            
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e
    
    def batch_insert_with_redistribution(self, new_requirements: List[Dict]) -> None:
        """Insert multiple requirements and handle conflicts"""
        if not new_requirements:
            return
        
        self.conn.execute("BEGIN TRANSACTION")
        try:
            # First, insert all new requirements
            for req in new_requirements:
                self.conn.execute(f"""
                    CREATE (:RequirementEntity {{
                        id: '{req['id']}',
                        title: '{req.get('title', '')}',
                        description: '{req.get('description', '')}',
                        priority: {req.get('priority', 128)}
                    }})
                """)
            
            # Check for collisions
            result = self.conn.execute("""
                MATCH (r:RequirementEntity)
                WITH r.priority AS p, count(r) AS cnt
                WHERE cnt > 1
                RETURN count(p) > 0 AS has_collisions
            """)
            
            if result.get_next()[0]:
                # Collisions exist - redistribute all
                self.conn.execute("COMMIT")  # Commit inserts first
                self.redistribute_priorities()  # Then redistribute
            else:
                self.conn.execute("COMMIT")
                
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e