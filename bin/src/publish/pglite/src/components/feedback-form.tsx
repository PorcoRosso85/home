'use client';

import { useState } from 'react';
import { Button, TextField, Label, Input, FieldError } from 'react-aria-components';
import { submitToR2 } from '../server/actions';

interface FeedbackFormData {
  name: string;
  email: string;
  message: string;
}

export const FeedbackForm = () => {
  const [formData, setFormData] = useState<FeedbackFormData>({
    name: '',
    email: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleInputChange = (field: keyof FeedbackFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      // Create FormData from form state
      const formDataToSubmit = new FormData();
      formDataToSubmit.append('name', formData.name);
      formDataToSubmit.append('email', formData.email);
      formDataToSubmit.append('message', formData.message);
      
      // Submit to R2 using server action
      const result = await submitToR2(formDataToSubmit);
      
      if (result.success) {
        console.log('Feedback submitted successfully:', result.filename);
        setSubmitStatus('success');
        
        // Reset form on success
        setFormData({ name: '', email: '', message: '' });
      } else {
        console.error('Server returned error:', result.message);
        setSubmitStatus('error');
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
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
        Feedback Form
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
              placeholder="Please share your feedback..."
            />
          </TextField>
        </div>

        <div style={{ marginTop: '20px' }}>
          <Button
            type="submit"
            style={buttonStyle}
            isDisabled={isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
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
            Thank you for your feedback! It has been submitted successfully.
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
            Sorry, there was an error submitting your feedback. Please try again.
          </div>
        )}
      </form>
    </section>
  );
};