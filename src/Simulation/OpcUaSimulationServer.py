from opcua import ua, Server


class OpcServerSimulation:
    NAME_SPACE = "Python_OPC_Server"

    def __init__(self, server_url="opc.tcp://127.0.0.1:4880/"):
        self.server = Server()

        self.server_url = server_url
        self.url = self.server_url

        self.server.set_endpoint(self.url)

        self.namespace_index = self.server.register_namespace(OpcServerSimulation.NAME_SPACE)

        self.node = self.server.get_objects_node()
        self.variables_object = self.node.add_object(self.namespace_index, "variables")

        self.security_policy = [ua.SecurityPolicyType.NoSecurity]

        self.server.set_security_policy(self.security_policy)

        self.server.start()

    def add_variable(self, node_identifier, initial_value=0, is_writable=True,
                     namespace_index=None, variable_name=None):

        if namespace_index is None:
            namespace_index = self.namespace_index

        if variable_name is None:
            variable_name = str(node_identifier)

        if type(node_identifier) == str:
            node_id = ua.NodeId(node_identifier, namespace_index)
        else:
            node_id = ua.NodeId(identifier=node_identifier, namespaceidx=namespace_index,
                                nodeidtype=ua.NodeIdType.Numeric)

        variable = self.variables_object.add_variable(nodeid=node_id, bname=str(variable_name),
                                                      val=initial_value)

        if is_writable:
            variable.set_writable()

        return variable

    def get_value(self, node_id):
        node = self.server.get_node(node_id)
        return node.get_value()

    def set_value(self, node_id, value):
        node = self.server.get_node(node_id)
        node.set_value(value)

    def get_node(self, node_id):
        return self.server.get_node(node_id)

    def kill(self):
        self.server.stop()

    def add_custom_variables(self):
        self.add_variable(node_identifier="PRODUCTION", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="ARRET", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="DEFECTTYPE", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="PRODUCTREFERENCE", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="Mold_open", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="prod_T27", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="prod_T45", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="prod_INJ5", initial_value=False, is_writable=True)
        self.add_variable(node_identifier="prod_INJ6", initial_value=False, is_writable=True)
        self.add_variable(node_identifier=579912, initial_value=0, is_writable=True)
        self.add_variable(node_identifier="Test", initial_value=0, is_writable=True, namespace_index=4)


if __name__ == "__main__":
    server = OpcServerSimulation()
    server.add_custom_variables()
