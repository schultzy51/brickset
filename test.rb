require 'savon'
require 'pry'

# create a client for the service
client = Savon.client(wsdl: 'http://brickset.com/api/v2.asmx?WSDL')

# client.operations
# => [:find_user, :list_users]

# call the 'findUser' operation
# response = client.call(:get_sets, message: {})

# response.body
binding.pry
