import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './PostJob.css';

const PostJob = () => {
  const [formData, setFormData] = useState({
    keywords: '',
    location: '',
    max_jobs: '',
    timeRange: '', // default to no time range
  });

  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('http://127.0.0.1:5000/search_jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        navigate('/GetJobs');
      } else {
        console.error('Failed to submit form');
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="keywords">Keywords:</label>
        <input
          type="text"
          id="keywords"
          name="keywords"
          value={formData.keywords}
          onChange={handleChange}
          required
        />
      </div>
      <div>
        <label htmlFor="location">Location:</label>
        <input
          type="text"
          id="location"
          name="location"
          value={formData.location}
          onChange={handleChange}
          required
        />
      </div>
      <div>
        <label htmlFor="max_jobs">Max Jobs:</label>
        <input
          type="number"
          id="max_jobs"
          name="max_jobs"
          value={formData.max_jobs}
          onChange={handleChange}
          required
        />
      </div>
      <div>
        <label htmlFor="timeRange">Time Range:</label>
        <select
          id="timeRange"
          name="timeRange"
          value={formData.timeRange}
          onChange={handleChange}
        >
          <option value="">None</option>
          <option value="3600">1 hour</option>
          <option value="86400">24 hours</option>
        </select>
      </div>
      <button type="submit">Submit</button>
    </form>
  );
};

export default PostJob;