class math_class:
    def __init__(self):
        print("Hi, I'm here")
        
    def min(self, list):
      lowest = list[0]
      for n in list:
        if n < lowest:
          lowest = n
    
      return lowest
      
    def max(self, list):
      greatest = list[0]
      for n in list:
        if n > greatest:
          greatest = n
    
      return greatest
    
    def sum(self, list):
      total = 0
      for n in list:
        total = total + n
        
      return total
    
    def average(self, list):
      avg = sum(list)/len(list)
      return avg
      
    def median(self, list):
      list.sort()
      length = len(list)
    
      if(length % 2 == 1):
        middle = (int) (length / 2)
        return list[middle]
      
      if(length % 2 == 0):
        middle = (int) (length / 2)
        avg = (list[middle] + list[middle-1]) / 2
        return avg
        
    def Q1(self, list):
      list.sort()
      q = (int) (len(list) / 4)
    
      return list[q]
      
    def Q3(self, list):
      list.sort()
    
      q = (int) (3 * len(list) / 4)
    
      return list[q]
    
  