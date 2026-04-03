import React, { useEffect, useState } from 'react';
import './GetJob.css';

const GetJob = () => {
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/get_jobs');
        if (!response.ok) {
          throw new Error('Failed to fetch jobs');
        }
        const data = await response.json();
        setJobs(data.jobs);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchJobs();
  }, []);

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="getjob-container">
      <h1 className="title">Job Listings</h1>
      {jobs.length === 0 ? (
        <p className="no-jobs">No jobs available.</p>
      ) : (
        <div className="jobs-grid">
          {jobs.map((job, index) => (
            <JobCard key={index} job={job} />
          ))}
        </div>
      )}
    </div>
  );
};

// Small subcomponent to render a job card with expandable description
const JobCard = ({ job }) => {
  const [expanded, setExpanded] = useState(false);

  const description = job.description || '';
  const PREVIEW_LEN = 120; // shorter preview
  const shortDesc = description.length > PREVIEW_LEN ? description.slice(0, PREVIEW_LEN) + '...' : description;

  return (
    <div className="job-card">
      <div className="job-header">
        {job.logo_tag && (
          <img src={job.logo_tag} alt={job.company + ' logo'} className="company-logo" />
        )}
        <h2 className="job-title">{job.title}</h2>
      </div>
      <p><strong>Company:</strong> {job.company}</p>
      <p><strong>Location:</strong> {job.location}</p>
      <p className="posted-date">Posted: {job.posted_date}</p>
      {job.time_note && <p className="time-note">{job.time_note}</p>}

      {description ? (
        <>
          <div className="description-label">Description:</div>
          {expanded ? (
            <>
              <p className="job-description">{description}</p>
              {description.length > PREVIEW_LEN && (
                <button className="toggle-desc" onClick={() => setExpanded(false)}>
                  Show less
                </button>
              )}
            </>
          ) : (
            <p className="job-description">
              {shortDesc.replace('...', '')}
              {description.length > PREVIEW_LEN && (
                <button className="toggle-desc inline" onClick={() => setExpanded(true)}>
                  ...Show more
                </button>
              )}
            </p>
          )}
        </>
      ) : (
        <>
          <div className="description-label">Description:</div>
          <p className="job-description">No description available.</p>
        </>
      )}

      <a
        href={job.job_link}
        target="_blank"
        rel="noopener noreferrer"
        className="view-job"
      >
        View Job
      </a>
    </div>
  );
};

export default GetJob;
