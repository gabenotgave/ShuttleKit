# AI Usage in ShuttleKit Development

This document provides transparency about how AI tools were used in the development of ShuttleKit.

## Overview

ShuttleKit was developed with assistance from various AI tools and models. This document outlines which tools were used for which aspects of the project, in the spirit of transparency and reproducibility.

## AI Tools Used

### Kiro (Claude Sonnet 4.5)

**Primary Use: Debugging, Documentation, and Testing**

- **Frontend Debugging**: Extensive use for troubleshooting React/Next.js issues and TypeScript type errors
- **Google Maps Integration**: Debugging map rendering issues and marker placement
- **Markdown Documentation**: Moderate usage for creating and formatting all project documentation including:
  - README.md
  - SETUP.md
  - ARCHITECTURE.md
  - CONTRIBUTING.md
  - This file (AI_USAGE.md)
- **Unit Tests**: Complete generation of pytest unit tests for:
  - `api/tests/api/test_geo.py` - Geospatial calculation tests
  - `api/tests/api/test_planning.py` - Route planning logic tests
  - `api/tests/api/test_chat.py` - Chat API endpoint tests
- **API Testing**: Full generation of Postman collection for API endpoint testing
  - `api/tests/postman/shuttlekit.postman_collection.json`
- **Test Coverage**: Ensuring comprehensive test coverage for core backend functionality

### Claude Sonnet 4.6 (Native Claude Website)

**Primary Use: Planning and Architecture**

- **Initial Idea Development**: Brainstorming and refining the core concept of a campus shuttle planning system
- **Feature Roadmapping**: Planning feature priorities and development phases
- **Architecture Design**: Discussing system architecture decisions, API design, and data models
- **Problem Solving**: High-level discussions about algorithmic approaches (route planning, geospatial calculations)

### v0 (Vercel GenAI)

**Primary Use: Frontend Boilerplate**

- **Next.js Project Structure**: Initial Next.js 16 project setup with App Router
- **UI Components**: Generation of shadcn/ui component library integration
- **Component Scaffolding**: Initial React component structure for:
  - Map display component
  - Search panel
  - Itinerary panel
  - Navbar
- **Styling Setup**: Tailwind CSS configuration and initial styling patterns

## Human-Written Code

While AI tools provided assistance, the following aspects involved substantial human input and decision-making:

### Core Logic
- **Geospatial Calculations** (`api/shuttlekit/geo.py`): Haversine formula implementation and nearest-stop algorithm
- **Route Planning** (`api/shuttlekit/planning.py`): Shuttle loop scheduling and trip planning logic
- **API Design**: Endpoint structure and response formats

### Configuration
- **Schedule Ingestion** (`api/ingestion/ingest.py`): LLM-based schedule extraction logic and geocoding integration
- **Config Schema**: Design of `config.json` structure for routes, stops, and schedules

### Integration
- **API-Frontend Communication**: Designing the contract between backend and frontend
- **CORS Configuration**: Security and cross-origin setup
- **Deployment Strategy**: Decisions about decoupled architecture and deployment options

## AI Limitations and Human Oversight

Throughout development, human oversight was critical for:

1. **Accuracy Verification**: Validating AI-generated code for correctness
2. **Security Review**: Ensuring proper security practices (API keys, CORS, etc.)
3. **Architecture Decisions**: Making final calls on system design and technology choices
4. **Business Logic**: Defining requirements and expected behavior
5. **Testing**: Manually testing the application end-to-end
6. **Documentation Review**: Ensuring documentation accuracy and completeness

## Ethical Considerations

### Transparency
This document exists to provide full transparency about AI usage in this project. We believe in being open about how AI tools contribute to software development.

### Attribution
All AI tools used are properly attributed above. The project acknowledges that some portions of code, documentation, and tests were AI-assisted or AI-generated.

### Learning and Understanding
While AI tools generated some code, the development process involved:
- Understanding all generated code before integration
- Modifying and adapting AI suggestions to fit project needs
- Learning from AI explanations and implementations
- Making informed decisions about when to use or reject AI suggestions

## Reproducibility

To reproduce this project's development approach:

1. **Planning Phase**: Use Claude or similar LLMs for brainstorming and architecture discussions
2. **Boilerplate Generation**: Use v0 or similar tools for initial frontend scaffolding
3. **Development**: Use Kiro or similar AI coding assistants for:
   - Debugging and error resolution
   - Documentation writing
   - Test generation
4. **Human Review**: Always review, test, and understand AI-generated code before committing

## Future AI Usage

As the project evolves, we expect continued AI assistance for:
- Debugging
- Documentation updates
- Test coverage expansion
- Performance optimization

All AI contributions will continue to be documented and attributed appropriately.

## Conclusion

AI tools were instrumental in accelerating ShuttleKit's development, particularly for boilerplate generation, testing, and documentation. However, the project's core logic, architecture decisions, and integration work involved significant human expertise and oversight.

We believe this hybrid approach—leveraging AI for productivity while maintaining human judgment and understanding—represents a responsible and effective way to build software in the AI era.

---

**Last Updated**: March 28, 2026

**Note**: This document will be updated as AI tools continue to be used in the project's development and maintenance.
