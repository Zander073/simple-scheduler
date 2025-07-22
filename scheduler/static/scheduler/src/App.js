function App() {
    // Simple routing based on current path
    const [currentRoute, setCurrentRoute] = React.useState(() => {
        return window.location.pathname.startsWith('/request') ? 'request' : 'calendar';
    });

    // Handle route changes
    const navigateTo = (route) => {
        setCurrentRoute(route);
        // Update URL without page reload
        window.history.pushState({}, '', route === 'calendar' ? '/' : `/${route}`);
    };

    // Listen for browser back/forward buttons
    React.useEffect(() => {
        const handlePopState = () => {
            const path = window.location.pathname;
            setCurrentRoute(path.startsWith('/request') ? 'request' : 'calendar');
        };

        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, []);

    return (
        <div className="container">
            {currentRoute === 'calendar' && <CalendarView />}
            {currentRoute === 'request' && <RequestView />}
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));