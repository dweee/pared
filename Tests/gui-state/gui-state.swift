import SwiftUI

struct GUIStateProbe: View {
  @GUIState private var enabled = false

  var body: some View {
    Toggle("Enabled", isOn: $enabled)
    Button("Toggle") { enabled.toggle() }
  }
}
