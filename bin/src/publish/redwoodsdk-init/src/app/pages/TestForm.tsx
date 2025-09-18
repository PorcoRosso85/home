export function TestForm() {
  return (
    <div style={{ padding: "20px" }}>
      <h1>Test Form</h1>
      <form method="POST" action="/api/test-submit">
        <div style={{ marginBottom: "10px" }}>
          <label htmlFor="name">Name:</label><br />
          <input type="text" id="name" name="name" required />
        </div>
        <div style={{ marginBottom: "10px" }}>
          <label htmlFor="email">Email:</label><br />
          <input type="email" id="email" name="email" required />
        </div>
        <div style={{ marginBottom: "10px" }}>
          <label htmlFor="message">Message:</label><br />
          <textarea id="message" name="message" rows={4} required />
        </div>
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}