'use client';

import { useState } from 'react';
import { Form, TextField, Label, Input, Button } from 'react-aria-components';

export const SimpleForm = () => {
  const [name, setName] = useState('');
  const [submitted, setSubmitted] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(name);
    setName('');
  };

  return (
    <section style={{
      border: '1px dashed #60a5fa',
      borderRadius: '2px',
      marginTop: '16px',
      marginLeft: '-16px',
      marginRight: '-16px',
      padding: '16px',
      fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      <Form onSubmit={handleSubmit}>
        <TextField
          value={name}
          onChange={setName}
          style={{ marginBottom: '16px' }}
        >
          <Label style={{
            display: 'block',
            marginBottom: '4px',
            fontSize: '0.875rem',
            fontWeight: 'bold'
          }}>
            Your Name
          </Label>
          <Input
            style={{
              width: '100%',
              padding: '8px',
              fontSize: '1rem',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
            placeholder="Enter your name"
          />
        </TextField>
        <Button
          type="submit"
          style={{
            backgroundColor: 'black',
            color: 'white',
            paddingLeft: '16px',
            paddingRight: '16px',
            paddingTop: '4px',
            paddingBottom: '4px',
            fontSize: '0.875rem',
            borderRadius: '2px',
            border: 'none',
            cursor: 'pointer',
            fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
          }}
        >
          Submit
        </Button>
      </Form>
      {submitted && (
        <p style={{ marginTop: '16px', color: '#059669' }}>
          Hello, {submitted}!
        </p>
      )}
    </section>
  );
};