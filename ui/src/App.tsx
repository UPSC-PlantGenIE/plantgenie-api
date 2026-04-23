import Navbar from './components/Navbar'
import Wizard from './components/Wizard'

function App() {
  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main>
        <Wizard />
      </main>
    </div>
  )
}

export default App
