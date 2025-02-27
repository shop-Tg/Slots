function App() {
    const [spinning, setSpinning] = React.useState(false);
    const [result, setResult] = React.useState(null);
    const [showProfile, setShowProfile] = React.useState(false);
    
    // Получаем данные из Telegram WebApp
    const tg = window.Telegram.WebApp;
    const user = {
        id: tg.initDataUnsafe?.user?.id || 'test',
        username: tg.initDataUnsafe?.user?.username || 'test_user',
        stars: 100
    };

    const handleSpin = () => {
        if (spinning) return;
        
        setSpinning(true);
        setResult(null);
        
        // Анимация вращения
        const wheel = document.querySelector('.roulette-wheel');
        const randomRotations = 5 + Math.random() * 5;
        wheel.style.transform = `rotate(${randomRotations * 360}deg)`;
        
        // Симулируем результат через 3 секунды
        setTimeout(() => {
            const gifts = [
                {name: "💝 15 Stars", value: 15},
                {name: "💝 25 Stars", value: 25},
                {name: "💝 35 Stars", value: 35},
                {name: "💝 50 Stars", value: 50},
                {name: "💝 100 Stars", value: 100},
                {name: "💝 250 Stars", value: 250}
            ];
            
            const randomGift = gifts[Math.floor(Math.random() * gifts.length)];
            setResult(randomGift);
            setSpinning(false);
        }, 3000);
    };
    
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-4xl font-bold">🎰 Crypto Slots</h1>
                <div className="flex items-center space-x-4">
                    <span className="text-xl">⭐ {user.stars}</span>
                    <button
                        onClick={() => setShowProfile(!showProfile)}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
                    >
                        {showProfile ? "Скрыть профиль" : "Показать профиль"}
                    </button>
                </div>
            </div>
            
            {showProfile && (
                <div className="profile-card mb-8">
                    <h2 className="text-2xl font-bold mb-4">Профиль игрока</h2>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="text-lg font-bold">ID</div>
                            <div className="text-2xl">{user.id}</div>
                        </div>
                        <div className="stat-card">
                            <div className="text-lg font-bold">Имя</div>
                            <div className="text-2xl">{user.username}</div>
                        </div>
                        <div className="stat-card">
                            <div className="text-lg font-bold">Звезды</div>
                            <div className="text-2xl">⭐ {user.stars}</div>
                        </div>
                    </div>
                </div>
            )}
            
            <div className="flex flex-col items-center mb-8">
                <div className="roulette-wheel mb-8">
                    <div className="roulette-center"></div>
                </div>
                
                <button
                    onClick={handleSpin}
                    disabled={spinning}
                    className={`spin-button ${spinning ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                    {spinning ? 'Крутим...' : 'Крутить!'}
                </button>
                
                {result && (
                    <div className="mt-8 text-center">
                        <h3 className="text-2xl font-bold mb-4">
                            🎉 Вы выиграли {result.name}!
                        </h3>
                        <button
                            onClick={() => {
                                tg.close();
                            }}
                            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg"
                        >
                            Забрать
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

// Инициализация приложения
ReactDOM.render(<App />, document.getElementById('root')); 