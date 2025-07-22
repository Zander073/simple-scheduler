function App() {
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
        <div className="container">
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
            
            <AppointmentCalendar />
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));