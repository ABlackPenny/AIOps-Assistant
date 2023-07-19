"""Controller for the use and management of probes.

The controller is the entry point for the Assistant to utilise the probes
that allows it to reach out into the environment and collect real time
information. The controller is a class that provides a unified interface
between the string based data used by the Assistants LLM and the raw data
that is generated by the indiviual probes.


Registering a Probe
-------------------
When a probe is to be added to the controller, it must be added to the
__probe_index list within the ProbeController class. This entry provides
the controller with the unique name of the probe, and function hooks to
obtain a list of supported callable functions and the ability to call
the listed function:

    {
        'name': 'probe_name',
        'list_function': probes.probe_name.function_list,
        'call_function': probes.probe_name.function_call,
    },
"""
import logging

# Probe modules registered with the controller
import probes.database

logger = logging.getLogger(__name__)
"""Configure the default logger for the module."""


class FunctionNotFoundError(Exception):
    """Error if a callable probe function could not be found.
    
    This should only be raised as a result of a program bug as the only
    functions that should be published by the controller are functions
    that we know about.

    Parameter
    ---------
    msg
        The name of the function that could not be found.
    """
    def __init__(self, msg) -> None:
        """Generate a error message for the exception."""
        self.msg = f'Probe callable function not found: {msg}'


class ProbeNotFoundError(Exception):
    """Error if a probe could not be found.
    
    This should only be raised as a result of a program bug as the only
    probes that should be reference are the ones internally configured
    within the controller.

    Parameter
    ---------
    msg
        The name of the probe that could not be found.
    """
    def __init__(self, msg) -> None:
        self.msg = f'Probe not found: {msg}'


class ProbeController:
    """Manages the brokering of function request and returning results to the Assistant.

    The Probe Controller class is the single interface to all probes that
    are configured within the application.

    Parameters
    ----------
    None
    """

    # List of all probes registered with the controller. Each list item is a
    # dictonary with the following values:
    #    name:          The name of the probe.
    #    list_function: Reference to the function that will provide the list
    #                   of callable functions.
    #    call_function: Referenct to the function call handler.
    __probe_index = [
        {
            'name': 'database',
            'list_function': probes.database.function_list,
            'call_function': probes.database.function_call,
        },
    ]


    # List of all known calling functions tagged with their parent probe.
    # Each list item is a dictonary with the following values:
    #    probe:    The name of the probe to which the function belongs.
    #    function: Dictonary of the function definition
    __function_index = []


    def __init__(self) -> None:
        """Identify all registered probes and collect all available functions.

        For all of the probes that are listed within the probe_index variable,
        get each ones provided functions and create a index of functions within
        function_index for use by the class instance.

        Parameters
        ----------
        None
        """
        for probe in self.__probe_index:
            for probe_func in probe['list_function']():
                self.__function_index.append({'probe': probe['name'], 'function': probe_func})


    # Search the probe_index for the requested probe name and return its
    # definition
    def __get_probe(self, name: str) -> dict:
        for probe in self.__probe_index:
            if probe['name'] == name:
                return probe
        raise ProbeNotFoundError(name)


    # Search the function_index for the requested function and return its
    # definition
    def __get_function(self, name: str) -> dict:
        for func in self.__function_index:
            if func['function']['name'] == name:
                return func
        raise FunctionNotFoundError(name)


    def function_list(self) -> list:
        """Generate a list of all registered probe functions.

        For each probe that has been registered within the probe_index
        list, generate a list of function definitions which can be
        used reference by the Assistant.

        Parameters
        ----------
        None

        Returns
        -------
        list
            List of dict for all functions provided by all probes
        """
        return_list = []
        for probe in self.__probe_index:
            return_list = return_list + probe['list_function']()
        return return_list


    def function_call(self, function_name: str, function_args: dict) -> str:
        """Execute the provided probe function and return the result.

        The function_name provided is used to search the function_index
        for a corresponding probe function to call. It is expected that
        the function name is unique across all probes, however the first
        instance of the function name found will be called.

        Once a calling function has been identified its specification is
        checked that the required arguments have been provided for its
        invocation and the function is called with its returned results
        returned from this function

        Parameters
        ----------
        function_name
            The name of the function to be called from the function_index.
        function_args
            Dictonary of argument values for the function to be called.

        Returns
        -------
        str
            Response from the called function as a string to be passed
            back to the LLM. Will return None on error.
        """
        try:
            # Get the probe to which this function belongs
            probe_function = self.__get_function(function_name)
            probe = self.__get_probe(probe_function['probe'])

            logger.debug(
                'Calling {0}.{1}():\n{2}'.format(
                    probe['name'],
                    function_name,
                    function_args,
                )
            )
            
            # Call the probe to execute function(args)
            probe_result = probe['call_function'](
                function_name, 
                function_args,
            )

            logger.debug(
                'Function result: {0}.{1}()\n{2}'.format(
                    probe['name'],
                    probe_function['function']['name'],
                    probe_result,
                )       
            )
            return probe_result
        
        except FunctionNotFoundError as err:
            # need to do something better than printing to the console
            print(err)
            return None

        except ProbeNotFoundError as err:
            # need to do something better than printing to the console
            print(err)
            return None
