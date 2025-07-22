const getCurrentWeekHeader = () => {
    const now = new Date();
    const currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const monday = new Date(now);
    
    // Go back to Monday of current week
    const daysToMonday = currentDay === 0 ? 6 : currentDay - 1;
    monday.setDate(now.getDate() - daysToMonday);
    
    // Get Friday (5 days after Monday)
    const friday = new Date(monday);
    friday.setDate(monday.getDate() + 4);
    
    // Format the header
    const mondayMonth = monday.toLocaleDateString('en-US', { month: 'short' });
    const fridayMonth = friday.toLocaleDateString('en-US', { month: 'short' });
    const mondayDate = monday.getDate();
    const fridayDate = friday.getDate();
    const year = monday.getFullYear();
    
    // If same month, show "Jul 21-25, 2025"
    // If different months, show "Jul 28 - Aug 1, 2025"
    if (mondayMonth === fridayMonth) {
        return `${mondayMonth} ${mondayDate}-${fridayDate}, ${year}`;
    } else {
        return `${mondayMonth} ${mondayDate} - ${fridayMonth} ${fridayDate}, ${year}`;
    }
};

function App() {
    return (
        <div className="container">
            <div className="header">
                <h1>{getCurrentWeekHeader()}</h1>
                <p>Current week</p>
            </div>
            
            <div className="calendar-placeholder">
                Calendar will go here...
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root')); 