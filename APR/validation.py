
from read import read
from pre_processing import pre_process
from apr_rg import rule_generator
from apr_cb_m1 import classifier_builder_m1
from apr_cb_m1 import is_satisfy
from functools import cmp_to_key
import time
import random

def sort_dict(val):
    def cmp_dict(a,b):
        s1=list(a.cond_set.keys())
        s2=list(b.cond_set.keys())
        # print("s1",s1,"s2",s2)
        for i in range(len(s1)):
            if s1[i]>s2[i]:
                return 1
            elif s1[i]<s2[i]:
                return -1

        return 1

    rule_list = list(val)
    rule_list.sort(key=cmp_to_key(cmp_dict))
    # print([x.cond_set for x in rule_list])
    return rule_list

# calculate the error rate of the classifier on the dataset
def get_error_rate(classifier, dataset):
    size = len(dataset)
    error_number = 0
    for case in dataset:
        is_satisfy_value = False
        for rule in classifier.rule_list:
            is_satisfy_value = is_satisfy(case, rule)
            if is_satisfy_value == True:
                break
        if is_satisfy_value == False:
            if classifier.default_class != case[-1]:
                error_number += 1
    return error_number / size

def acc(apr,test):
    temp=[]
    actual=[x[-1] for x in test]
    count=0
    for i in range(len(test)):
        flag1=True
        for j in range(len(apr.rule_list)):
            flag=True
            for item in apr.rule_list[j].cond_set:
                if test[i][item]!=apr.rule_list[j].cond_set[item]:
                    flag=False
                    break
            if flag:
                temp.append(apr.rule_list[j].class_label)
                if temp[-1]==actual[i]:
                    count+=1
                flag1=False
                break

        if flag1:
            temp.append(apr.default_class)
            if temp[-1]==actual[i]:
                count+=1

    res=count/len(test)
    return res

# 10-fold cross-validations on apr
def cross_validate_m1_without_prune(data_path, scheme_path,class_first=False, minsup=0.1, minconf=0.6):
    data, attributes, value_type = read(data_path, scheme_path)
    if class_first:
        for i in range(len(data)):
            a=data[i].pop(0)
            data[i].append(a)
        a=attributes.pop(0)
        attributes.append(a)
        b=value_type.pop(0)
        value_type.append(b)
        # print(data[0])
    random.shuffle(data)
    dataset = pre_process(data, attributes, value_type)

    block_size = int(len(dataset) / 10)
    split_point = [k * block_size for k in range(0, 10)]
    split_point.append(len(dataset))

    apr_rg_total_runtime = 0
    apr_cb_total_runtime = 0
    total_car_number = 0
    total_classifier_rule_num = 0
    error_total_rate = 0
    acc_total=0
    for k in range(len(split_point)-1):
        print("\nRound %d:" % k)

        training_dataset = dataset[:split_point[k]] + dataset[split_point[k+1]:]
        test_dataset = dataset[split_point[k]:split_point[k+1]]

        start_time = time.time()
        cars = rule_generator(training_dataset, minsup, minconf)
        end_time = time.time()
        apr_rg_runtime = end_time - start_time
        apr_rg_total_runtime += apr_rg_runtime

        arr=list(cars.rules_list)
        max=-1

        for i in range(len(arr)):
            if len(arr[i].cond_set)>max:
                max=len(arr[i].cond_set)
        T=[[] for i in range(max)]
        for i in range(len(arr)):
            T[len(arr[i].cond_set)-1].append(arr[i])
        u=[]
        for i in range(len(T)):
            T[i]=sort_dict(T[i])

            for j in T[i]:
                u.append(j)
        # print([u[i].cond_set for i in range(len(u))])
        apr_rg_total_runtime += apr_rg_runtime

        start_time = time.time()
        # print("----------")
        classifier= classifier_builder_m1(cars, training_dataset,minsup,len(training_dataset),u)


        end_time = time.time()
        apr_cb_runtime = (end_time - start_time)/10
        apr_cb_total_runtime += apr_cb_runtime

        classifier.print()
        res=acc(classifier,test_dataset)
        acc_total+=res

        error_rate = get_error_rate(classifier, test_dataset)
        error_total_rate += error_rate

        total_car_number += len(cars.rules)
        total_classifier_rule_num += len(classifier.rule_list)

        print("accuracy:",(res*100))
        print("No. of CARs : ",len(cars.rules_list))
        print("apr-RG's run time : s" ,apr_rg_runtime)
        print("apr-CB run time :  s" ,apr_cb_runtime)
        print("No. of rules in classifier of apr: " ,len(classifier.rule_list))

    print("\n Average APR's accuracy :",(acc_total/10*100))
    print("Average No. of CARs : ",(total_car_number / 10))
    print("Average apr-RG's run time : " ,(apr_rg_total_runtime / 10))
    print("Average apr-CB run time :  " ,(apr_cb_total_runtime / 10))
    print("Average No. of rules in classifier of apr: " ,(total_classifier_rule_num / 10))



if __name__ == "__main__":
    # using the relative path, all data sets are stored in datasets directory
    test_data_path = 'Dataset/ASD.data'
    test_scheme_path = 'Dataset/ASD.names'

    # just choose one mode to experiment by removing one line comment and running
    min_support=0.2
    min_conf=0.7
    is_class_first=False
    cross_validate_m1_without_prune(test_data_path, test_scheme_path,is_class_first,min_support,min_conf)
