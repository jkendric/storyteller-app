import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import CharactersPage from './pages/CharactersPage'
import ScenariosPage from './pages/ScenariosPage'
import StoriesPage from './pages/StoriesPage'
import StoryReaderPage from './pages/StoryReaderPage'
import NewStoryPage from './pages/NewStoryPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/characters" element={<CharactersPage />} />
        <Route path="/scenarios" element={<ScenariosPage />} />
        <Route path="/stories" element={<StoriesPage />} />
        <Route path="/stories/new" element={<NewStoryPage />} />
        <Route path="/stories/:storyId" element={<StoryReaderPage />} />
      </Routes>
    </Layout>
  )
}

export default App
