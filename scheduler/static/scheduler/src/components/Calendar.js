function Calendar({ currentWeekStart }) {
    // Generate time slots from 9 AM to 4 PM
    const timeSlots = [];
    for (let hour = 9; hour <= 16; hour++) {
        const time = `${hour}:00`;
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

    return (
        <div className="calendar">
            {/* Header row with time and weekday columns */}
            <div className="calendar-header">
                <div className="time-header">Time</div>
                {weekdays.map((day, index) => (
                    <div key={day} className="day-header">
                        <div className="day-name">{day}</div>
                        <div className="day-number">{dayNumbers[index]}</div>
                    </div>
                ))}
            </div>
            
            {/* Time slots rows */}
            {timeSlots.map((time) => (
                <div key={time} className="calendar-row">
                    <div className="time-slot">{time}</div>
                    {weekdays.map((day) => (
                        <div key={`${day}-${time}`} className="calendar-cell">
                            {/* Appointment slots will go here */}
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}

