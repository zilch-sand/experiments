import './App.css';
import { Header } from './components/Header';
import { JsonFormsDemo } from './components/JsonFormsDemo';

const App = () => {
  return (
    <>
      <Header />
      <main>
        <JsonFormsDemo />
      </main>
    </>
  );
};

export default App;
