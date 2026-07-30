# Developer Documentation Checklist

Verify every item before declaring the developer track complete.

## Setup and operation

- [ ] Local environment setup
- [ ] Dependency installation
- [ ] Build, test, and lint commands, each verified against the build manifest or CI config
- [ ] Environment variables: name, purpose, default, required or optional — never a value
- [ ] Debugging tips
- [ ] CI/CD notes
- [ ] Contribution workflow

## Structure

- [ ] Repository layout with the purpose of each top-level directory
- [ ] Architecture overview: components, responsibilities, data flow
- [ ] Boundaries: what the system deliberately does not do

## API

- [ ] Every API version group identified, with how a caller selects a version
- [ ] One page per resource per version; versions never merged onto one page
- [ ] Each endpoint: method, path, auth, parameters with types and required flags
- [ ] Each endpoint: response shape, every status code, worked example
- [ ] Version differences recorded per resource
- [ ] Deprecated and removed versions marked as such

## Code reference

- [ ] Public functions with full signatures, annotations, and defaults
- [ ] Public classes with base classes, attributes, and methods
- [ ] Errors and exceptions, with the conditions that raise them
- [ ] Extension points listed, with which methods to override
- [ ] A worked subclass or interface implementation example

## Accuracy

- [ ] Signatures copied from source, not paraphrased
- [ ] No endpoint, parameter, or version invented
- [ ] Known gaps recorded as open questions rather than written as implemented

## Safety

- [ ] No credential, token, key, or connection string appears anywhere
- [ ] No `[REDACTED:...]` marker reproduced in the output
