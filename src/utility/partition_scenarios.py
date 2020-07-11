import csv
task_time = {}
import time
class MaxHeapArr():
    def __init__(self,m):
        self.__array = []
        self.__last_index = -1
        self.__machines = m

    def push(self, value):
        self.__array.append(value)
        self.__last_index += 1
        self.__siftup(self.__last_index)

    def pop(self):
        if self.__last_index == -1:
            raise IndexError("Can't pop from empty heap")
        root_value = self.__array[0]
        
        if self.len_heap() > 0:  # more than one element in the heap
            self.__array.remove(root_value)
            #self.__array[0] = self.__array[self.__last_index]
            if(self.len_heap()>0 ): self.__siftdown(0)
        self.__last_index -= 1
        return root_value
        
    def len_heap(self):
        return len(self.__array)

    def get_heap_el(self,i):
        if(i < self.len_heap()):
            return self.__array[i]
        else:
            return None
    
    def peek(self):
        if not self.__array:
            return None
        return self.__array[0]
    
    def print_all_elements(self):
        for i in range(0,len(self.__array)):
            print (self.__array[i])
        return 

    def __siftdown(self, index):
        current_value = self.__array[index]
        left_child_index, left_child_value = self.__get_left_child(index)
        right_child_index, right_child_value = self.__get_right_child(index)
        best_child_index, best_child_value = (right_child_index, right_child_value) if right_child_index\
        is not None and self.comparer(right_child_value, left_child_value) else (left_child_index, left_child_value)
        if best_child_index is not None and self.comparer(best_child_value, current_value):
            self.__array[index], self.__array[best_child_index] =\
                best_child_value, current_value
            self.__siftdown(best_child_index)
        return

    def __siftup(self, index):
        current_value = self.__array[index]
        parent_index, parent_value = self.__get_parent(index)
        if index > 0 and self.comparer(current_value, parent_value):
            self.__array[parent_index], self.__array[index] = current_value, parent_value
            self.__siftup(parent_index)
        return
    
    def comparer(self, value1, value2):
        # value1 and value2 will be array of arrays
        return my_sum(value1,self.__machines) > my_sum(value2,self.__machines)

    def __get_parent(self, index):
        if index == 0:
            return None, None
        parent_index =  (index - 1) // 2
        return parent_index, self.__array[parent_index]

    def __get_left_child(self, index):
        left_child_index = 2 * index + 1
        if left_child_index > self.len_heap()-1:
            return None, None
        return left_child_index, self.__array[left_child_index]

    def __get_right_child(self, index):
        right_child_index = 2 * index + 2
        if right_child_index > self.len_heap()-1:
            return None, None
        return right_child_index, self.__array[right_child_index]


def main(task_time_arr,machines):
        global task_time
        task_time = task_time_arr
        task_arr = []
        task_arr_temp = sorted(task_time.items(),key=lambda x: x[1])
        for i in range(0,len(task_arr_temp)):
            task_arr.append(task_arr_temp[i][0])
        
        if(machines==0): 
            return
        if(machines >= len(task_arr)) :
            max_time = max(task_time.items(), key=lambda x:x[1])[1]
            partitions = {"seq_partitions":task_arr,"activeIce":machines,"totalTime":max_time}
            return partitions
        else:
            return multi_partition_kk(task_time,task_arr,machines)


def convert_time_to_seconds(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds) 
      

def multi_partition_kk(task_time,task_arr,machines):
    start_time = time.time()
    partitions = {}
    #As explained in multi-partition paper =>
    ''' A heuristic much better than greedy was called set differencing by its authors [Karmarkar and Karp, 1982], but is usually referred to as the KK heuristic. It places the two largest
        numbers in different subsets, without determining which subset each goes into. This is equivalent to replacing the two
        numbers with their difference. For example, placing 8 in subset A and 7 in subset B is equivalent to placing their difference of 1 in subset A, since we can always subtract the same
        amount from both sets without affecting the solution. Swapping their positions is equivalent to placing the 1 in subset B.
        he KK heuristic repeatedly replaces the two largest numbers
        with their difference, inserting the new number in the sorted
        order, until there is only one number left, which is the final
        partition difference. In our example, this results in the series
        of sets (8,7,6,5,4), (6,5,4,1), (4,1,1), (3,1), (2). Some additional book-keeping is required to extract the actual partition,
        which in this case is (7,5,4) and (8,6), with a partition difference of 16-14=2. '''
    #creating a max-heap , as i will need the largest element in each iteration and a new element(after merge) will be pushed .
    #initial elements in my heap will be partitions with a single task in each .
    ''' Eg: If there (8,7,6,5,4) are to be scheduled in 3 machines , my initial heap elements will be : 
        ([[8],[],[]] , [[7],[],[]] , [[6],[],[]] , [[5],[],[]]..........)''' 
    main_arr = MaxHeapArr(machines) 
    for i in range(0,len(task_arr)):
        list_for_curr_el = [[task_arr[i]]]
        for j in range(0,machines-1):
            list_for_curr_el.append([])
        main_arr.push(list_for_curr_el)
    arr_len = len(task_arr)
    # now we start merging our partitions , till only one final partition remains , which will be our solution closest to optimal .
    while(arr_len!=1):
        temp_main_arr = main_arr
        main_arr = merge_largest(temp_main_arr)
        arr_len = arr_len-1
    sum_for_machines = []
    machine_time = {}
    for i in range(0,len(main_arr.get_heap_el(0))):
        sum_for_machines.append(my_array_sum(main_arr.get_heap_el(0)[i]))
        machine_time[my_array_sum(main_arr.get_heap_el(0)[i])] = main_arr.get_heap_el(0)[i]
    '''    
    print("Partitions => "+ str(main_arr.get_heap_el(0)))
    print("Total Machines => "+str(machines))
    print("Machine time => "+str(sum_for_machines))
    print("Max-Min difference between partitions => " + str(max(sum_for_machines) - min(sum_for_machines)))
    print("Total Time (in seconds)=> " + str(max(sum_for_machines)))
    print("Total Time (in Hours:Minutes:Seconds)=> " + convert_time_to_seconds(max(sum_for_machines)))
    print("Elapsed Time (in seconds) => "+ str(time.time() - start_time))
    print("---------------------- kk-partition Ends -----------------------")
    '''
    partitions = {"seq_partitions":main_arr.get_heap_el(0),"activeIce":machines,"totalTime":max(sum_for_machines),"iceTime":sum_for_machines,"machine_time":machine_time}
    return partitions

def merge_largest(arr):
    ''' This will merge the largest 2 elements of heap , remove them and push the merged element 
        An element can be considered as a partition .
        Eg: If we have 3 machines , and our elements are [[9,10], [13], [12]] and [[16], [14], [13]]
        The smallest arrays will be merged with largest and new element after merge will be : [[9,10,13] ,[14,13], [16,12]]
        Which will be sorted to form [[9,10,13] ,[16,12], [14,13]] and will be pushed to heap .'''
    el1 = arr.pop()
    #print "el1=>",el1
    el2 = arr.pop()
    #print "el2=>",el2
    el3 = []
    len_el = len(el1)
    for i in range(0,len_el):
        joined_val = el1[i]+el2[len_el-1-i]
        el3.append(joined_val)
    #print "elnew=>",el3
    #print "----------------------"
    el3_sorted = sorted(el3,key = lambda x:my_array_sum(x) , reverse=True)
    arr.push(el3_sorted)
    return arr
 
def my_array_sum(z):
    # z will be an array of tasks 
    '''Array elements will be tasks , and sum is calculated by accessing their values from task_time object'''
    ret_sum = 0
    for i in range(0,len(z)):
        ret_sum = ret_sum + task_time[z[i]]
    return ret_sum
 
def my_sum(y,machines):
    # heap elements are sorted on the basis of their sum , which is calculated as :
    ''' a heap element is an array of arrays .
        Eg: [[8],[7],[4,2]]
        min_el_sum is 4+2 = 6 , which will be subtracted from each element .
        Its sum is : sum(8,7,(4+2))- len*min_el_sum'''
    min_sum = my_array_sum(min(y, key=lambda x:my_array_sum(x)))
    total_sum = 0
    for i in range(0,len(y)):
        total_sum = total_sum+my_array_sum(y[i])
    if(len(y)!=machines) : min_sum =0
    return total_sum-(min_sum*len(y))

if __name__== "__main__":
  main()
  