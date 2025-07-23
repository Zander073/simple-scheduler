function App() {
    // Simple routing based on current path
    const [currentRoute, setCurrentRoute] = React.useState(() => {
        const path = window.location.pathname;
        if (path === '/request/submitted/') return 'request-submitted';
        if (path.startsWith('/request')) return 'request';
        return 'calendar';
    });

    // Handle route changes
    const navigateTo = (route) => {
        setCurrentRoute(route);
        // Update URL without page reload
        let path = '/';
        if (route === 'request') path = '/request/';
        else if (route === 'request-submitted') path = '/request/submitted/';
        window.history.pushState({}, '', path);
    };

    // Listen for browser back/forward buttons
    React.useEffect(() => {
        const handlePopState = () => {
            const path = window.location.pathname;
            if (path === '/request/submitted/') setCurrentRoute('request-submitted');
            else if (path.startsWith('/request')) setCurrentRoute('request');
            else setCurrentRoute('calendar');
        };

        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, []);

    return (
        <div className="container">
            {currentRoute === 'calendar' && <CalendarView />}
            {currentRoute === 'request' && <RequestView navigateTo={navigateTo} />}
            {currentRoute === 'request-submitted' && <RequestSubmittedView navigateTo={navigateTo} />}
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));