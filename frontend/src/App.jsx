import './App.css'
import {Route,Routes,BrowserRouter} from 'react-router-dom';
import { Dashboard } from './pages/Dasboard';
import { Signup } from './pages/Signup';
import { Signin } from './pages/Signin';
import { Historyy } from './pages/Historyy';
import { Search } from './pages/Search';

function App() {
  
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard/>}></Route>
        <Route path="/signup" element={<Signup/>}></Route>
        <Route path="/signin" element={<Signin/>}></Route>
        <Route path="/history" element={<Historyy/>}></Route>
        <Route path="/search" element={<Search/>}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
