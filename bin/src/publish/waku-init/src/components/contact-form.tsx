'use client';

import { useState } from 'react';
import { Button, TextField, Label, Input } from 'react-aria-components';
import { submitToR2 } from '../server/actions';
import type { ContactFormData } from '../domain/mod';

export const ContactForm = () => {
  const [formData, setFormData] = useState<ContactFormData>({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleInputChange = (field: keyof ContactFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      // Create FormData with all form fields
      const formDataObj = new FormData();
      formDataObj.append('name', formData.name);
      formDataObj.append('email', formData.email);
      formDataObj.append('subject', formData.subject);
      formDataObj.append('message', formData.message);

      // Submit to R2 using server action
      const result = await submitToR2(formDataObj);
      
      if (result.success) {
        console.log('Contact form submitted successfully:', result.filename);
        setSubmitStatus('success');
        
        // Reset form on success
        setFormData({ name: '', email: '', subject: '', message: '' });
      } else {
        console.error('Server returned error:', result.message);
        setSubmitStatus('error');
      }
    } catch (error) {
      console.error('Failed to submit contact form:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const baseStyle = {
    fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
  };

  const fieldStyle = {
    marginBottom: '16px'
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '4px',
    fontSize: '0.875rem',
    fontWeight: 'bold',
    ...baseStyle
  };

  const inputStyle = {
    width: '100%',
    padding: '8px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    fontSize: '0.875rem',
    ...baseStyle
  };

  const textareaStyle = {
    ...inputStyle,
    minHeight: '120px',
    resize: 'vertical' as const
  };

  const buttonStyle = {
    backgroundColor: isSubmitting ? '#6b7280' : '#000000',
    color: 'white',
    padding: '8px 16px',
    fontSize: '0.875rem',
    borderRadius: '4px',
    border: 'none',
    cursor: isSubmitting ? 'not-allowed' : 'pointer',
    ...baseStyle
  };

  const containerStyle = {
    border: '1px dashed #60a5fa',
    borderRadius: '4px',
    padding: '20px',
    marginTop: '16px',
    maxWidth: '500px',
    ...baseStyle
  };

  return (
    <section style={containerStyle}>
      <h2 style={{ 
        marginTop: 0, 
        marginBottom: '16px', 
        fontSize: '1.25rem',
        ...baseStyle 
      }}>
        Contact Us
      </h2>
      
      <form onSubmit={handleSubmit}>
        <div style={fieldStyle}>
          <TextField>
            <Label style={labelStyle}>Name</Label>
            <Input
              style={inputStyle}
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              required
              disabled={isSubmitting}
              placeholder="Your full name"
            />
          </TextField>
        </div>

        <div style={fieldStyle}>
          <TextField>
            <Label style={labelStyle}>Email</Label>
            <Input
              style={inputStyle}
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              required
              disabled={isSubmitting}
              placeholder="your.email@example.com"
            />
          </TextField>
        </div>

        <div style={fieldStyle}>
          <TextField>
            <Label style={labelStyle}>Subject</Label>
            <Input
              style={inputStyle}
              value={formData.subject}
              onChange={(e) => handleInputChange('subject', e.target.value)}
              required
              disabled={isSubmitting}
              placeholder="What is your inquiry about?"
            />
          </TextField>
        </div>

        <div style={fieldStyle}>
          <TextField>
            <Label style={labelStyle}>Message</Label>
            <textarea
              style={textareaStyle}
              value={formData.message}
              onChange={(e) => handleInputChange('message', e.target.value)}
              required
              disabled={isSubmitting}
              placeholder="Please describe your inquiry in detail..."
            />
          </TextField>
        </div>

        <div style={{ marginTop: '20px' }}>
          <Button
            type="submit"
            style={buttonStyle}
            isDisabled={isSubmitting}
          >
            {isSubmitting ? 'Sending...' : 'Send Message'}
          </Button>
        </div>

        {submitStatus === 'success' && (
          <div style={{
            marginTop: '12px',
            padding: '8px',
            backgroundColor: '#d1fae5',
            border: '1px solid #10b981',
            borderRadius: '4px',
            color: '#065f46',
            fontSize: '0.875rem',
            ...baseStyle
          }}>
            Thank you for contacting us! Your message has been sent successfully.
          </div>
        )}

        {submitStatus === 'error' && (
          <div style={{
            marginTop: '12px',
            padding: '8px',
            backgroundColor: '#fee2e2',
            border: '1px solid #ef4444',
            borderRadius: '4px',
            color: '#991b1b',
            fontSize: '0.875rem',
            ...baseStyle
          }}>
            Sorry, there was an error sending your message. Please try again.
          </div>
        )}
      </form>
    </section>
  );
};