Leveraging **Rodney** for Chrome automation and **Showboat** for executable markdown documentation, this project showcases a reproducible workflow for exploring and documenting the pydantic-jsonforms-demo—a full-stack app combining FastAPI/Pydantic on the backend with React/JSONForms on the frontend. The experiment illustrates how browser automation can capture application states, while Showboat ensures demonstrations remain verifiable and up-to-date as code evolves. Key features include single-source validation (Pydantic-defined), dynamic form generation, support for complex/nested data structures, and dual client-server validation. Despite environment limitations (no Chrome for Rodney), Playwright proved to be a viable alternative for browser automation.

Key findings:
- Automated documentation with [Showboat](https://github.com/unifyai/showboat) enhances reproducibility and maintenance.
- Rodney (or alternatives like Playwright) simplifies browser interaction for demos and testing ([Rodney](https://github.com/unifyai/rodney)).
- Dynamic forms generated from Pydantic schemas facilitate robust type-safe validation across frontend and backend.
- Treating documentation as code allows continual verification that walkthroughs remain accurate.
