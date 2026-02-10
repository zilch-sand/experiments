import logo from '../assets/logo.svg';

export const Header = () => (
  <header className="app-header">
    <img src={logo} className="app-logo" alt="JSONForms + FastAPI logo" />
    <h1 className="app-title">Portfolio Builder</h1>
    <p className="app-subtitle">
      JSONForms UI powered by Pydantic schemas and FastAPI validation.
    </p>
  </header>
);
