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

    // State for appointments and clients
    const [appointments, setAppointments] = React.useState([]);
    const [clients, setClients] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    const [notifications, setNotifications] = React.useState([]);
    const [isModalOpen, setIsModalOpen] = React.useState(false);

    // WebSocket connection
    React.useEffect(() => {
        const ws = new WebSocket('ws://localhost:8001/ws/appointments/');
        
        ws.onopen = function(e) {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'appointment_request') {
                const newNotification = {
                    id: Date.now(), // Unique ID for each notification
                    type: 'success',
                    message: `New appointment request from ${data.data.client_name}`,
                    urgent: data.data.is_urgent,
                    timestamp: new Date(),
                    client_name: data.data.client_name,
                    start_time: data.data.start_time
                };
                
                setNotifications(prev => {
                    const updated = [...prev, newNotification];
                    return updated;
                });
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

    // Fetch clients
    const fetchClients = async () => {
        try {
            const response = await fetch('/api/clients/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setClients(data);
        } catch (err) {
            console.error('Error fetching clients:', err);
        }
    };

    // Fetch appointments and clients on component mount
    React.useEffect(() => {
        fetchAppointments();
        fetchClients();
    }, []); // Only fetch on mount for now, we can add week dependency later if needed

    // Function to format start time for display in browser timezone
    const formatStartTime = (startTimeString) => {
        if (!startTimeString) return 'TBD';
        
        const date = new Date(startTimeString);
        const dateOptions = {
            weekday: 'long',
            month: 'short',
            day: 'numeric'
        };
        const timeOptions = {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        };
        
        const dateStr = date.toLocaleDateString('en-US', dateOptions);
        const timeStr = date.toLocaleTimeString('en-US', timeOptions);
        
        return `${dateStr} at ${timeStr}`;
    };

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
    
    const goToCurrentWeek = () => {
        const now = new Date();
        const currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
        const currentWeekStart = new Date(now);
        
        // Go back to Monday of current week
        const daysToMonday = currentDay === 0 ? 6 : currentDay - 1;
        currentWeekStart.setDate(now.getDate() - daysToMonday);
        
        setCurrentWeekStart(currentWeekStart);
    };
    
    return (
        <>
            {notifications.length > 0 && (
                <div className="notifications-container">
                    {notifications.map((notification, index) => (
                        <div 
                            key={notification.id} 
                            className={`notification ${notification.type} ${notification.urgent ? 'urgent' : ''}`}
                            style={{order: index}}
                        >
                            {notification.urgent ? (
                                <div className="notification-content">
                                    <button 
                                        className="notification-close"
                                        onClick={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
                                    >
                                        ×
                                    </button>
                                    
                                    <div className="critical-header">
                                        <svg className="warning-icon" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2L1 21h22L12 2zm0 3.17L19.83 19H4.17L12 5.17zM11 16h2v2h-2zm0-6h2v4h-2z"/>
                                        </svg>
                                        <span className="critical-label">Critical</span>
                                    </div>
                                    
                                    <div className="client-name">{notification.client_name}</div>
                                    <div className="crisis-message">
                                        Client experiencing severe dissociative episodes with reality distortion. Immediate psychological stabilization required.
                                    </div>
                                    
                                    <div className="action-section">
                                        <div className="action-title">
                                            <svg className="action-icon" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                            </svg>
                                            SimpleSchedule Action:
                                        </div>
                                        <ul className="action-list">
                                            <li>Emergency appointment auto-scheduled for {formatStartTime(notification.start_time)}</li>
                                            <li>Client was communicated with via secure emergency text message and phone call</li>
                                            <li>Crisis intervention protocol summary generated and added to client record</li>
                                        </ul>
                                    </div>
                                </div>
                            ) : (
                                <div className="notification-content">
                                    <button 
                                        className="notification-close"
                                        onClick={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
                                    >
                                        ×
                                    </button>
                                    
                                    <div className="info-header">
                                        <svg className="info-icon" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                                        </svg>
                                        <span className="info-label">Info</span>
                                    </div>
                                    
                                    <div className="client-name">{notification.client_name}</div>
                                    <div className="request-message">
                                        Client requested to reschedule Tuesday session due to child's school emergency. Alternative time requested for same week if available.
                                    </div>
                                    
                                    <div className="action-section">
                                        <div className="action-title">
                                            <svg className="action-icon" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                            </svg>
                                            SimpleSchedule Action:
                                        </div>
                                        <ul className="action-list">
                                            <li>Appointment request received and queued for review</li>
                                            <li>Client was communicated with via secure patient portal and email confirmation</li>
                                            <li>Schedule change confirmation letter generated and added to client record</li>
                                        </ul>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
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
                    <button className="current-week-button" onClick={goToCurrentWeek}>
                        Current Week
                    </button>
                    <button className="add-appointment-button" onClick={() => setIsModalOpen(true)}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        Add Appointment
                    </button>
                </div>
            </div>
            
            {loading && <div className="loading">Loading appointments...</div>}
            {error && <div className="error">Error loading appointments: {error}</div>}
            {!loading && !error && (
                <Calendar currentWeekStart={currentWeekStart} appointments={appointments} />
            )}
            
            <AddAppointmentModal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                clients={clients}
                onAppointmentCreated={fetchAppointments}
            />
        </>
    );
}