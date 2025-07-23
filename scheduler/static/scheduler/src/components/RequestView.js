function RequestView({ navigateTo = () => {} }) {
    const [isUrgent, setIsUrgent] = React.useState(false);
    const [timePreference, setTimePreference] = React.useState(2); // 9 AM = 0, 11 AM = 2
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [submitMessage, setSubmitMessage] = React.useState('');

    // Update slider background based on value
    const updateSliderBackground = (element, value, max) => {
        const percentage = (value / max) * 100;
        element.style.background = `linear-gradient(to right, #007bff 0%, #007bff ${percentage}%, #ddd ${percentage}%, #ddd 100%)`;
    };

    // Set initial slider backgrounds on component mount
    React.useEffect(() => {
        const timeSlider = document.getElementById('time-slider');
        
        if (timeSlider) {
            updateSliderBackground(timeSlider, timePreference, 7);
        }
    }, []);

    // Convert time preference slider value to actual time
    const getTimeFromSlider = (value) => {
        const hour = 9 + value; // 9 AM + slider value
        if (hour === 12) return '12:00 PM';
        if (hour > 12) return `${hour - 12}:00 PM`;
        return `${hour}:00 AM`;
    };

    // Convert slider value to hour for API
    const getHourFromSlider = (value) => {
        return 9 + value; // 9 AM + slider value
    };

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubmitMessage('');

        try {
            const response = await fetch('/api/requests/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    is_urgent: isUrgent,
                    time_preference: getHourFromSlider(timePreference)
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Redirect to success page
                if (typeof navigateTo === 'function') {
                    navigateTo('request-submitted');
                } else {
                    // Fallback: redirect manually
                    window.location.href = '/request/submitted/';
                }
            } else {
                setSubmitMessage(`Error: ${data.error || 'Failed to submit request'}`);
            }
        } catch (error) {
            setSubmitMessage(`Error: ${error.message}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="request-view">
            <h1>Request an appointment</h1>
            
            <form onSubmit={handleSubmit}>
                <div className="form-section">
                    <div className="checkbox-container">
                        <label htmlFor="urgent-checkbox">Urgent?</label>
                        <input
                            type="checkbox"
                            id="urgent-checkbox"
                            name="is_urgent"
                            checked={isUrgent}
                            onChange={(e) => setIsUrgent(e.target.checked)}
                            className="checkbox"
                        />
                    </div>
                </div>

                <div className="form-section">
                    <label htmlFor="time-slider">Time of day preference</label>
                    <div className="slider-container">
                        <input
                            type="range"
                            id="time-slider"
                            name="time_preference"
                            min="0"
                            max="7"
                            value={timePreference}
                            onChange={(e) => {
                                const value = parseInt(e.target.value);
                                setTimePreference(value);
                                updateSliderBackground(e.target, value, 7);
                            }}
                            onInput={(e) => updateSliderBackground(e.target, parseInt(e.target.value), 7)}
                            className="slider"
                        />
                    </div>
                    <div className="slider-hint">Current: {getTimeFromSlider(timePreference)}</div>
                </div>
                
                <div className="form-section">
                    <button 
                        type="submit" 
                        className="submit-button"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Submitting...' : 'Request appointment'}
                    </button>
                </div>

                {submitMessage && (
                    <div className={`submit-message ${submitMessage.includes('Error') ? 'error' : 'success'}`}>
                        {submitMessage}
                    </div>
                )}
            </form>
        </div>
    );
} 