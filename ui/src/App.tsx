import Navbar from './components/Navbar'
import Wizard from './components/wizard/Wizard'

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
