function Calendar({ currentWeekStart, appointments }) {
    // Generate time slots from 9 AM to 4 PM
    const timeSlots = [];
    for (let hour = 9; hour <= 16; hour++) {
        const time = hour === 12 ? '12:00 PM' : 
                    hour > 12 ? `${hour - 12}:00 PM` : 
                    `${hour}:00 AM`;
        timeSlots.push(time);
    }

    // Generate weekday headers with dynamic dates
    const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    const dayNumbers = [];
    
    // Calculate the dates for each weekday (Monday = 1, Tuesday = 2, etc.)
    for (let i = 0; i < 5; i++) {
        const dayDate = new Date(currentWeekStart);
        dayDate.setDate(currentWeekStart.getDate() + i);
        dayNumbers.push(dayDate.getDate().toString()); // No leading zeros
    }

    // Determine which column is today (if any)
    const today = new Date();
    const todayIndex = dayNumbers.findIndex((dayNum, index) => {
        const dayDate = new Date(currentWeekStart);
        dayDate.setDate(currentWeekStart.getDate() + index);
        return dayDate.toDateString() === today.toDateString();
    });

    // Helper function to get appointments for a specific day and time
    const getAppointmentsForSlot = (dayIndex, timeSlot) => {
        const dayDate = new Date(currentWeekStart);
        dayDate.setDate(currentWeekStart.getDate() + dayIndex);
        
        // Convert time slot back to hour for comparison
        const hour = timeSlot.includes('PM') && !timeSlot.includes('12') 
            ? parseInt(timeSlot.split(':')[0]) + 12 
            : timeSlot.includes('12 PM') 
                ? 12 
                : parseInt(timeSlot.split(':')[0]);
        
        return appointments.filter(appointment => {
            const appointmentDate = new Date(appointment.start_time);
            return appointmentDate.toDateString() === dayDate.toDateString() && 
                   appointmentDate.getHours() === hour;
        });
    };

    return (
        <div className="calendar">
            {/* Header row with time and weekday columns */}
            <div className="calendar-header">
                <div className="time-header">Time</div>
                {weekdays.map((day, index) => (
                    <div 
                        key={day} 
                        className={`day-header ${index === todayIndex ? 'today-header' : ''}`}
                    >
                        <div className="day-name">{day}</div>
                        <div className="day-number">{dayNumbers[index]}</div>
                    </div>
                ))}
            </div>
            
            {/* Time slots rows */}
            {timeSlots.map((time) => (
                <div key={time} className="calendar-row">
                    <div className="time-slot">{time}</div>
                    {weekdays.map((day, index) => {
                        const slotAppointments = getAppointmentsForSlot(index, time);
                        return (
                            <div 
                                key={`${day}-${time}`} 
                                className={`calendar-cell ${index === todayIndex ? 'today-cell' : ''}`}
                            >
                                {slotAppointments.map((appointment, appIndex) => (
                                    <div key={appointment.id} className="appointment">
                                        {appointment.client.first_name} {appointment.client.last_name}
                                    </div>
                                ))}
                            </div>
                        );
                    })}
                </div>
            ))}
        </div>
    );
}

