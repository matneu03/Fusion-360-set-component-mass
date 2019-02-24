import adsk.core, adsk.fusion, adsk.cam, traceback

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection
        cmdDefs = ui.commandDefinitions

        # Create a button command definition
        button = cmdDefs.addButtonDefinition('buttonId', 
                                                   'Set Component Mass', 
                                                   'Set component mass in [g]')
        
        # Connect to the command created event
        set_mass = setMassCommandCreatedEventHandler()
        button.commandCreated.add(set_mass)
        handlers.append(set_mass)
        
        # Execute the command
        button.execute()
        
        # Keep the script running.
        adsk.autoTerminate(False)
    except: 
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the commandCreated event.
class setMassCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        
        # Get the command
        cmd = eventArgs.command

        # Get the CommandInputs collection to create new command inputs.            
        inputs = cmd.commandInputs

        # Create the value input to get the desired mass
        mass_desired = inputs.addValueInput('mass', 'Mass [g]', 
                                           '', adsk.core.ValueInput.createByReal(100))

        # Connect to the execute event.
        onExecute = setMassExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

# Event handler for the execute event. 
class setMassExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):

        ui = None
        try:
            # Setup necessary objects
            app = adsk.core.Application.get()
            ui  = app.userInterface        
            design = app.activeProduct
            
            if not design:
                ui.messageBox('No active Fusion design', 'No Design')
                return
            
            # Get input arguments
            event_args = adsk.core.CommandEventArgs.cast(args)
            inputs = event_args.command.commandInputs
            mass_desired = inputs.item(0).value
    
            # Cast the active component (for development purposes)
            activeComp = adsk.fusion.Component.cast(design.activeComponent)
            
            # Make an object collection containing the active component
            compCollection = adsk.core.ObjectCollection.create()
            compCollection.add(activeComp)
        
            # Calculate the desired density if value != 0
            physProps = design.physicalProperties(compCollection)   # Try second arg LowCalculationAccuracy, and try changing it

            if not physProps.volume:
                ui.messageBox('The current design has no volume. Aborting.')
                adsk.terminate()
                return
            
            density_desired = float(mass_desired) / physProps.volume * 10e2  
            
            # Copy the current material and set the new material density
            materials = design.materials
            material_name = activeComp.name
            material_old = activeComp.material.name
            materials.addByCopy(activeComp.material, material_name)
            density = materials.itemByName(material_name).materialProperties.itemByName("Density")
            density.value = density_desired
                        
            # Final messages
            ui.messageBox('The desired mass was set using the material named "' + material_name + '".\n\n' + "This material is similar to the component's previous material except for the updated density.\n\nRemember to re-run this script if the volume of the component is updated.")
            
        except:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

        adsk.terminate()
           
def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # Delete the command definition.
        cmdDef = ui.commandDefinitions.itemById('buttonId')
        if cmdDef:
            cmdDef.deleteMe()            
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))