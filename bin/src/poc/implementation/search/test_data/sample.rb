# Ruby sample
class Person
  attr_reader :name, :age
  
  def initialize(name, age)
    @name = name
    @age = age
  end
  
  def greet
    puts "Hello, I'm #{@name}"
  end
end

def create_person(name, age)
  Person.new(name, age)
end

# Main
person = create_person("Charlie", 35)
person.greet