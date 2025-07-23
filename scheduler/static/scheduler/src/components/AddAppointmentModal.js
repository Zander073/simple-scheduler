function AddAppointmentModal({ isOpen, onClose, clients, onAppointmentCreated }) {
    const [selectedClient, setSelectedClient] = React.useState('');
    const [selectedDate, setSelectedDate] = React.useState('');
    const [selectedTime, setSelectedTime] = React.useState('09:00');

    // Set default date to today when modal opens
    React.useEffect(() => {
        if (isOpen) {
            const today = new Date();
            const year = today.getFullYear();
            const month = String(today.getMonth() + 1).padStart(2, '0');
            const day = String(today.getDate()).padStart(2, '0');
            setSelectedDate(`${year}-${month}-${day}`);
        }
    }, [isOpen]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!selectedClient || !selectedDate || !selectedTime) {
            alert('Please fill in all required fields');
            return;
        }
        
        try {
            // Create ISO datetime string with timezone offset
            const dateTimeString = `${selectedDate}T${selectedTime}:00`;
            const dateTime = new Date(dateTimeString);
            const startTime = dateTime.toISOString();
            

            
            const response = await fetch('/api/appointments/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                },
                body: JSON.stringify({
                    client: selectedClient,
                    start_time: startTime
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to create appointment');
            }
            
            const appointment = await response.json();
            console.log('Appointment created:', appointment);
            
            // Close modal and reset form
            onClose();
            
            // Refresh the calendar to show the new appointment
            if (onAppointmentCreated) {
                onAppointmentCreated();
            }
            
            // Show success message
            alert('Appointment scheduled successfully!');
            
        } catch (error) {
            console.error('Error creating appointment:', error);
            alert(`Error: ${error.message}`);
        }
    };

    const handleCancel = () => {
        setSelectedClient('');
        setSelectedDate('');
        setSelectedTime('09:00');
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal">
                <div className="modal-header">
                    <div className="modal-title">
                        <h2>Schedule New Session</h2>
                        <p>Create a new therapy session appointment</p>
                    </div>
                    <button className="modal-close" onClick={handleCancel}>
                        ×
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="client-select">Client Name</label>
                        <select
                            id="client-select"
                            value={selectedClient}
                            onChange={(e) => setSelectedClient(e.target.value)}
                            required
                        >
                            <option value="">Select a client...</option>
                            {clients.map(client => (
                                <option key={client.id} value={client.id}>
                                    {client.full_name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="date-input">Date</label>
                            <input
                                type="date"
                                id="date-input"
                                value={selectedDate}
                                onChange={(e) => setSelectedDate(e.target.value)}
                                min={new Date().toISOString().split('T')[0]}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="time-input">Time</label>
                            <input
                                type="time"
                                id="time-input"
                                value={selectedTime}
                                onChange={(e) => setSelectedTime(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn-secondary" onClick={handleCancel}>
                            Cancel
                        </button>
                        <button type="submit" className="btn-primary">
                            Schedule Session
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}