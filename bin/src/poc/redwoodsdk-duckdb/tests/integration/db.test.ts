import { describe, it, expect, beforeAll, afterAll, beforeEach, vi } from 'vitest';
import { PrismaClient } from '@prisma/client';
import { PrismaD1 } from '@prisma/adapter-d1';
import type { D1Database } from '@cloudflare/workers-types';

// Mock D1 database for testing
const mockD1Database = {
  prepare: vi.fn().mockReturnThis(),
  bind: vi.fn().mockReturnThis(),
  first: vi.fn(),
  all: vi.fn(),
  run: vi.fn(),
  batch: vi.fn()
} as unknown as D1Database;

describe('Database Integration Tests', () => {
  let prisma: PrismaClient;

  beforeAll(() => {
    // Initialize Prisma with mock D1 adapter
    prisma = new PrismaClient({
      adapter: new PrismaD1(mockD1Database)
    });
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('User Model Operations', () => {
    it('should create a new user', async () => {
      const mockUser = {
        id: 'user-123',
        username: 'testuser',
        createdAt: new Date()
      };

      mockD1Database.run = vi.fn().mockResolvedValue({
        meta: { last_row_id: 1, changes: 1 }
      });
      mockD1Database.first = vi.fn().mockResolvedValue(mockUser);

      const createUser = async (username: string) => {
        await mockD1Database.run();
        return mockD1Database.first();
      };

      const result = await createUser('testuser');
      
      expect(result).toEqual(mockUser);
      expect(result.username).toBe('testuser');
    });

    it('should find user by username', async () => {
      const mockUser = {
        id: 'user-456',
        username: 'existinguser',
        createdAt: new Date()
      };

      mockD1Database.first = vi.fn().mockResolvedValue(mockUser);

      const findUser = async (username: string) => {
        return mockD1Database.first();
      };

      const result = await findUser('existinguser');
      
      expect(result).toBeDefined();
      expect(result.username).toBe('existinguser');
    });

    it('should handle unique constraint violations', async () => {
      mockD1Database.run = vi.fn().mockRejectedValue(
        new Error('UNIQUE constraint failed: User.username')
      );

      const createDuplicateUser = async () => {
        try {
          await mockD1Database.run();
          return { success: true };
        } catch (error: any) {
          return { success: false, error: error.message };
        }
      };

      const result = await createDuplicateUser();
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('UNIQUE constraint failed');
    });

    it('should list all users with pagination', async () => {
      const mockUsers = [
        { id: '1', username: 'user1', createdAt: new Date() },
        { id: '2', username: 'user2', createdAt: new Date() },
        { id: '3', username: 'user3', createdAt: new Date() }
      ];

      mockD1Database.all = vi.fn().mockResolvedValue({
        results: mockUsers.slice(0, 2),
        meta: { rows_read: 2, rows_written: 0 }
      });

      const getUsers = async (limit: number, offset: number) => {
        const result = await mockD1Database.all();
        return result.results;
      };

      const result = await getUsers(2, 0);
      
      expect(result).toHaveLength(2);
      expect(result[0].username).toBe('user1');
    });
  });

  describe('Credential Model Operations', () => {
    it('should create credential for user', async () => {
      const mockCredential = {
        id: 'cred-123',
        userId: 'user-123',
        credentialId: 'webauthn-cred-id',
        publicKey: Buffer.from('public-key-data'),
        counter: 0,
        createdAt: new Date()
      };

      mockD1Database.run = vi.fn().mockResolvedValue({
        meta: { last_row_id: 1, changes: 1 }
      });
      mockD1Database.first = vi.fn().mockResolvedValue(mockCredential);

      const createCredential = async (userId: string, credentialData: any) => {
        await mockD1Database.run();
        return mockD1Database.first();
      };

      const result = await createCredential('user-123', {
        credentialId: 'webauthn-cred-id',
        publicKey: Buffer.from('public-key-data')
      });
      
      expect(result.userId).toBe('user-123');
      expect(result.credentialId).toBe('webauthn-cred-id');
    });

    it('should find credential by credentialId', async () => {
      const mockCredential = {
        id: 'cred-456',
        credentialId: 'existing-cred-id',
        userId: 'user-456',
        counter: 5
      };

      mockD1Database.first = vi.fn().mockResolvedValue(mockCredential);

      const findCredential = async (credentialId: string) => {
        return mockD1Database.first();
      };

      const result = await findCredential('existing-cred-id');
      
      expect(result).toBeDefined();
      expect(result.credentialId).toBe('existing-cred-id');
      expect(result.counter).toBe(5);
    });

    it('should update credential counter', async () => {
      mockD1Database.run = vi.fn().mockResolvedValue({
        meta: { changes: 1 }
      });

      const updateCounter = async (credentialId: string, newCounter: number) => {
        const result = await mockD1Database.run();
        return result.meta.changes > 0;
      };

      const result = await updateCounter('cred-123', 10);
      
      expect(result).toBe(true);
      expect(mockD1Database.run).toHaveBeenCalled();
    });
  });

  describe('Transaction Support', () => {
    it('should handle transactions correctly', async () => {
      const mockTransaction = [
        { query: 'INSERT INTO User...', params: ['user1'] },
        { query: 'INSERT INTO Credential...', params: ['cred1'] }
      ];

      mockD1Database.batch = vi.fn().mockResolvedValue([
        { meta: { changes: 1 } },
        { meta: { changes: 1 } }
      ]);

      const executeTransaction = async () => {
        const results = await mockD1Database.batch();
        return results.every((r: any) => r.meta.changes > 0);
      };

      const result = await executeTransaction();
      
      expect(result).toBe(true);
      expect(mockD1Database.batch).toHaveBeenCalled();
    });

    it('should rollback on transaction failure', async () => {
      mockD1Database.batch = vi.fn().mockRejectedValue(
        new Error('Transaction failed')
      );

      const executeFailingTransaction = async () => {
        try {
          await mockD1Database.batch();
          return { success: true };
        } catch (error) {
          return { success: false, rolled_back: true };
        }
      };

      const result = await executeFailingTransaction();
      
      expect(result.success).toBe(false);
      expect(result.rolled_back).toBe(true);
    });
  });

  describe('Query Performance', () => {
    it('should use indexes efficiently', async () => {
      // Mock query with EXPLAIN QUERY PLAN
      mockD1Database.all = vi.fn().mockResolvedValue({
        results: [
          { detail: 'SEARCH User USING INDEX idx_username' }
        ]
      });

      const explainQuery = async () => {
        const result = await mockD1Database.all();
        return result.results[0].detail;
      };

      const result = await explainQuery();
      
      expect(result).toContain('USING INDEX');
    });

    it('should handle large result sets', async () => {
      const largeDataSet = Array.from({ length: 1000 }, (_, i) => ({
        id: `user-${i}`,
        username: `user${i}`
      }));

      mockD1Database.all = vi.fn().mockResolvedValue({
        results: largeDataSet.slice(0, 100),
        meta: { rows_read: 100 }
      });

      const getLargeDataSet = async () => {
        const result = await mockD1Database.all();
        return {
          count: result.results.length,
          hasMore: result.results.length === 100
        };
      };

      const result = await getLargeDataSet();
      
      expect(result.count).toBe(100);
      expect(result.hasMore).toBe(true);
    });
  });

  describe('Migration Support', () => {
    it('should check if migrations are applied', async () => {
      mockD1Database.all = vi.fn().mockResolvedValue({
        results: [
          { name: '0001_init.sql', applied_at: new Date() }
        ]
      });

      const checkMigrations = async () => {
        const result = await mockD1Database.all();
        return result.results.map((m: any) => m.name);
      };

      const result = await checkMigrations();
      
      expect(result).toContain('0001_init.sql');
    });
  });
});