describe('Chat widget modalities', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('supports inline mode for embedded layouts', () => {
    cy.get('[data-testid="mode-select"]').select('inplace');
    cy.get('[data-testid="chat-panel-inline"]').should('be.visible');
    cy.get('[data-testid="chat-input"]').type('Mensaje inline{enter}');
    cy.get('[data-testid="chat-messages"]').contains('Mensaje inline');
  });

  it('opens and closes from a floating button launcher', () => {
    cy.get('[data-testid="mode-select"]').select('floating');

    cy.get('[data-testid="chat-panel-floating"]').should('not.exist');
    cy.get('[data-testid="chat-launcher"]').click();
    cy.get('[data-testid="chat-panel-floating"]').should('be.visible');

    cy.get('[data-testid="chat-input"]').type('Hola desde floating{enter}');
    cy.get('[data-testid="chat-messages"]').contains('Hola desde floating');

    cy.get('[aria-label="Cerrar chat"]').click();
    cy.get('[data-testid="chat-panel-floating"]').should('not.exist');
  });

  it('renders a modal overlay when requested', () => {
    cy.get('[data-testid="mode-select"]').select('modal');

    cy.get('[data-testid="chat-panel-modal"]').should('not.exist');
    cy.get('[data-testid="chat-launcher"]').click();

    cy.get('[data-testid="chat-overlay"]').should('be.visible');
    cy.get('[data-testid="chat-panel-modal"]').should('be.visible');

    cy.get('[data-testid="chat-input"]').type('Mensaje en modal');
    cy.get('[data-testid="chat-send"]').click();
    cy.get('[data-testid="chat-messages"]').contains('Mensaje en modal');

    cy.get('[data-testid="chat-overlay"]').click('topLeft');
    cy.get('[data-testid="chat-panel-modal"]').should('not.exist');
  });

  it('anchors the assistant mode on the left and stays persistent', () => {
    cy.get('[data-testid="mode-select"]').select('assistant');

    cy.get('[data-testid="chat-panel-assistant"]').should('be.visible');
    cy.get('[aria-label="Cerrar chat"]').click();
    cy.get('[data-testid="chat-panel-assistant"]').should('not.exist');

    cy.get('[data-testid="chat-launcher"]').click();
    cy.get('[data-testid="chat-panel-assistant"]').should('be.visible');
  });
});
