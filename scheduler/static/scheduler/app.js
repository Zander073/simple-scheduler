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

const getWeekDescription = (targetWeekStart) => {
    const now = new Date();
    const currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const currentWeekStart = new Date(now);
    
    // Go back to Monday of current week
    const daysToMonday = currentDay === 0 ? 6 : currentDay - 1;
    currentWeekStart.setDate(now.getDate() - daysToMonday);
    
    // Calculate difference in weeks
    const diffTime = targetWeekStart.getTime() - currentWeekStart.getTime();
    const diffWeeks = Math.round(diffTime / (1000 * 60 * 60 * 24 * 7));
    
    if (diffWeeks === 0) {
        return "Current week";
    } else if (diffWeeks === 1) {
        return "Next week";
    } else if (diffWeeks === -1) {
        return "1 week ago";
    } else if (diffWeeks > 1) {
        return `${diffWeeks} weeks from now`;
    } else {
        return `${Math.abs(diffWeeks)} week${Math.abs(diffWeeks) === 1 ? '' : 's'} ago`;
    }
};

function App() {
    // Get the current week's Monday for comparison
    let now = new Date();
    let currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
    let currentWeekStart = new Date(now);
    
    // Go back to Monday of current week
    let daysToMonday = currentDay === 0 ? 6 : currentDay - 1;
    currentWeekStart.setDate(now.getDate() - daysToMonday);
    
    return (
        <div className="container">
            <div className="header">
                <h1>{getCurrentWeekHeader()}</h1>
                <p>{getWeekDescription(currentWeekStart)}</p>
            </div>
            
            <div className="calendar-placeholder">
                Calendar will go here...
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root')); 