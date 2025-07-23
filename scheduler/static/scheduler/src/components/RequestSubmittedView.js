function RequestSubmittedView({ navigateTo }) {
    return (
        <div className="request-view">
            <h1>Your request was submitted successfully</h1>
            <div className="form-section">
                <button 
                    type="button" 
                    className="submit-button"
                    onClick={() => navigateTo('request')}
                >
                    Request another appointment
                </button>
            </div>
        </div>
    );
} 