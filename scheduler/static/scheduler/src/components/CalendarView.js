function CalendarView() {
    // Initialize state with current week's Monday
    const [currentWeekStart, setCurrentWeekStart] = React.useState(() => {
        const now = new Date();
        const currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
        const monday = new Date(now);
        
        // Go back to Monday of current week
        const daysToMonday = currentDay === 0 ? 6 : currentDay - 1;
        monday.setDate(now.getDate() - daysToMonday);
        return monday;
    });

    // State for appointments
    const [appointments, setAppointments] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    const [notification, setNotification] = React.useState(null);

    // WebSocket connection
    React.useEffect(() => {
        const ws = new WebSocket('ws://localhost:8001/ws/appointments/');
        
        ws.onopen = function(e) {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'appointment_request') {
                setNotification({
                    type: 'success',
                    message: `New appointment request from ${data.data.client_name}`,
                    urgent: data.data.is_urgent
                });
                
                // Auto-hide notification after 5 seconds
                setTimeout(() => {
                    setNotification(null);
                }, 5000);
            }
        };
        
        ws.onclose = function(e) {
            console.log('WebSocket disconnected');
        };
        
        ws.onerror = function(e) {
            console.log('WebSocket error:', e);
        };
        
        return () => {
            ws.close();
        };
    }, []);

    // Fetch appointments
    const fetchAppointments = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await fetch('/api/appointments/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setAppointments(data);
        } catch (err) {
            setError(err.message);
            console.error('Error fetching appointments:', err);
        } finally {
            setLoading(false);
        }
    };

    // Fetch appointments on component mount and when week changes
    React.useEffect(() => {
        fetchAppointments();
    }, []); // Only fetch on mount for now, we can add week dependency later if needed

    const goToPreviousWeek = () => {
        const prevWeek = new Date(currentWeekStart);
        prevWeek.setDate(currentWeekStart.getDate() - 7);
        setCurrentWeekStart(prevWeek);
    };

    const goToNextWeek = () => {
        const nextWeek = new Date(currentWeekStart);
        nextWeek.setDate(currentWeekStart.getDate() + 7);
        setCurrentWeekStart(nextWeek);
    };
    
    return (
        <>
            {notification && (
                <div className={`notification ${notification.type} ${notification.urgent ? 'urgent' : ''}`}>
                    <div className="notification-content">
                        <span className="notification-message">{notification.message}</span>
                        <button 
                            className="notification-close"
                            onClick={() => setNotification(null)}
                        >
                            ×
                        </button>
                    </div>
                </div>
            )}
            
            <div className="header">
                <div className="header-content">
                    <h1>{getWeekHeader(currentWeekStart)}</h1>
                    <p>{getWeekDescription(currentWeekStart)}</p>
                </div>
                <div className="header-actions">
                    <button className="nav-button" onClick={goToPreviousWeek}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="15,18 9,12 15,6"></polyline>
                        </svg>
                    </button>
                    <button className="nav-button" onClick={goToNextWeek}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="9,18 15,12 9,6"></polyline>
                        </svg>
                    </button>
                </div>
            </div>
            
            {loading && <div className="loading">Loading appointments...</div>}
            {error && <div className="error">Error loading appointments: {error}</div>}
            {!loading && !error && (
                <Calendar currentWeekStart={currentWeekStart} appointments={appointments} />
            )}
        </>
    );
}