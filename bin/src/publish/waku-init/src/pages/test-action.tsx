import { submitForm } from '../server/actions';

export default async function TestActionPage() {
  // Server Component that triggers the action on load
  console.log('[TestActionPage] Server component rendering');
  
  // Create test FormData
  const testData = new FormData();
  testData.append('name', 'Test User');
  testData.append('email', 'test@example.com');
  testData.append('message', 'Testing console output from server component');
  
  // Call the server action directly
  console.log('[TestActionPage] Calling submitForm...');
  const result = await submitForm(testData);
  console.log('[TestActionPage] Result:', result);
  
  return (
    <div>
      <h1>Test Action Page</h1>
      <p>This page calls the server action directly on render.</p>
      <pre>{JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}