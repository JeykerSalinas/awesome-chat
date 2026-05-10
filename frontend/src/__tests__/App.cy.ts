import App from '../App.vue'
import router from '../router'

describe('App', () => {
  it('mounts and renders properly', () => {
    cy.mount(App, {
      global: {
        plugins: [router],
      },
    })
    cy.get('[data-testid="chat-preview"]').should('exist')
  })
})
