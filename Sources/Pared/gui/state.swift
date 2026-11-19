import SwiftUI

// SDK 27's State macro requires Apple's SwiftUIMacros plugin, which the
// standalone Nix toolchain does not include. Select the existing property
// wrapper directly so state and projected bindings keep their usual semantics.
typealias GUIState<Value> = SwiftUI.State<Value>
