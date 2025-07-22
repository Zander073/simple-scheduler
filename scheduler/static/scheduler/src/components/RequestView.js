function RequestView() {
    const [isUrgent, setIsUrgent] = React.useState(false);
    const [timePreference, setTimePreference] = React.useState(2); // 9 AM = 0, 11 AM = 2

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

    return (
        <div className="request-view">
            <h1>Request an appointment</h1>
            
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
                <button type="submit" className="submit-button">
                    Request appointment
                </button>
            </div>
        </div>
    );
} 