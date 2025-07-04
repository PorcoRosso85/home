/**
 * Real KuzuDB WASM Client Tests (CommonJS)
 * 規約準拠: test_{機能}_{条件}_{結果}
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { KuzuEventClient } = require('./kuzu_client_real.cjs');

test('test_kuzu_client_initialization_creates_schema', async () => {
  const client = new KuzuEventClient('client1');
  await client.initialize();
  
  // Verify schema by trying to query empty tables
  const users = await client.getUsers();
  assert.equal(users.length, 0);
  
  const posts = await client.getPosts();
  assert.equal(posts.length, 0);
});

test('test_executeTemplate_with_create_user_stores_in_kuzu', async () => {
  const client = new KuzuEventClient('client1');
  await client.initialize();
  
  const event = await client.executeTemplate('CREATE_USER', {
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  });
  
  // Verify event generated
  assert.equal(event.template, 'CREATE_USER');
  assert.equal(event.params.name, 'Alice');
  assert.ok(event.id.startsWith('evt_'));
  
  // Verify stored in KuzuDB
  const users = await client.getUsers();
  assert.equal(users.length, 1);
  assert.equal(users[0]['u.name'], 'Alice');
  assert.equal(users[0]['u.email'], 'alice@example.com');
});

test('test_executeTemplate_with_update_user_modifies_data', async () => {
  const client = new KuzuEventClient('client1');
  await client.initialize();
  
  // Create user
  await client.executeTemplate('CREATE_USER', {
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  });
  
  // Update user
  await client.executeTemplate('UPDATE_USER', {
    id: 'u1',
    name: 'Alice Smith'
  });
  
  // Verify update
  const users = await client.getUsers();
  assert.equal(users[0]['u.name'], 'Alice Smith');
  assert.equal(users[0]['u.email'], 'alice@example.com'); // Email preserved
});

test('test_executeTemplate_with_follow_creates_relationship', async () => {
  const client = new KuzuEventClient('client1');
  await client.initialize();
  
  // Create users
  await client.executeTemplate('CREATE_USER', {
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  });
  
  await client.executeTemplate('CREATE_USER', {
    id: 'u2',
    name: 'Bob',
    email: 'bob@example.com'
  });
  
  // Create follow relationship
  await client.executeTemplate('FOLLOW_USER', {
    followerId: 'u1',
    targetId: 'u2'
  });
  
  // Verify relationship
  const follows = await client.getFollows();
  assert.equal(follows.length, 1);
  assert.equal(follows[0].follower, 'u1');
  assert.equal(follows[0].target, 'u2');
});

test('test_executeTemplate_with_create_post_links_to_author', async () => {
  const client = new KuzuEventClient('client1');
  await client.initialize();
  
  // Create user
  await client.executeTemplate('CREATE_USER', {
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  });
  
  // Create post
  await client.executeTemplate('CREATE_POST', {
    id: 'p1',
    content: 'Hello KuzuDB!',
    authorId: 'u1'
  });
  
  // Verify post created
  const posts = await client.getPosts();
  assert.equal(posts.length, 1);
  assert.equal(posts[0]['p.content'], 'Hello KuzuDB!');
  assert.equal(posts[0]['p.authorId'], 'u1');
});

test('test_executeTemplate_with_delete_post_removes_node', async () => {
  const client = new KuzuEventClient('client1');
  await client.initialize();
  
  // Setup
  await client.executeTemplate('CREATE_USER', {
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  });
  
  await client.executeTemplate('CREATE_POST', {
    id: 'p1',
    content: 'To be deleted',
    authorId: 'u1'
  });
  
  // Verify post exists
  let posts = await client.getPosts();
  assert.equal(posts.length, 1);
  
  // Delete post
  await client.executeTemplate('DELETE_POST', {
    postId: 'p1'
  });
  
  // Verify deletion
  posts = await client.getPosts();
  assert.equal(posts.length, 0);
});

test('test_getEvents_returns_all_executed_events', async () => {
  const client = new KuzuEventClient('client1');
  await client.initialize();
  
  // Execute multiple templates
  await client.executeTemplate('CREATE_USER', {
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  });
  
  await client.executeTemplate('CREATE_USER', {
    id: 'u2',
    name: 'Bob',
    email: 'bob@example.com'
  });
  
  await client.executeTemplate('FOLLOW_USER', {
    followerId: 'u1',
    targetId: 'u2'
  });
  
  // Verify events
  const events = client.getEvents();
  assert.equal(events.length, 3);
  assert.equal(events[0].template, 'CREATE_USER');
  assert.equal(events[1].template, 'CREATE_USER');
  assert.equal(events[2].template, 'FOLLOW_USER');
});

test('test_event_checksum_is_consistent', async () => {
  const client1 = new KuzuEventClient('client1');
  const client2 = new KuzuEventClient('client2');
  
  await client1.initialize();
  await client2.initialize();
  
  const params = {
    id: 'u1',
    name: 'Alice',
    email: 'alice@example.com'
  };
  
  const event1 = await client1.executeTemplate('CREATE_USER', params);
  const event2 = await client2.executeTemplate('CREATE_USER', params);
  
  // Same template and params should produce same checksum
  assert.equal(event1.checksum, event2.checksum);
});